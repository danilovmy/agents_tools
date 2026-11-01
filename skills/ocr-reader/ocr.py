import json
import logging
import os
import shutil
import subprocess
import sys

# Load model
from argparse import ArgumentParser
from pathlib import Path

import bbox_align
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
from docuwarp.unwarp import Unwarp
from dotenv import dotenv_values
from PIL import Image

ROOT = Path(__file__).resolve().parent
settings = {**dotenv_values(ROOT / '.env', interpolate=False, encoding='utf-8-sig'), **os.environ}

logger = logging.getLogger(__name__)
handler = logging.FileHandler(Path(__file__).parent / "logger.log", encoding="utf-8")
handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))
logger.addHandler(handler)

MODEL_SIZE = "medium"
ARCHIVE_DIR = ROOT / 'data' / 'archive'
model = {MODEL_SIZE: None}

def align(extract_info):
    vertices = []
    words = []

    for obj in extract_info['words']:
        obj["geometry"] = sorted(obj["geometry"], key=lambda x: x[0])
        tl, bl, tr, br = [*sorted(obj["geometry"][:2], key=lambda x: x[1]), *sorted(obj["geometry"][2:], key=lambda x: x[1])]
        obj["geometry"] = [tl, tr, br, bl]
        if (tl == tr) or (br == bl) or (tl == bl) or (tr == br):
            logger.error(f'Geometry error {obj["geometry"]}')
            continue
        if obj["crop_orientation"]["value"] == 180:
            obj["value"] = obj["value"][::-1]

        vertices.append(obj["geometry"])
        words.append(obj["value"])


    boundaries = [[0,0],[1,0],[1,1],[0,1]]
    
    logger.info('align worlds')
    lines = bbox_align.process(vertices, boundaries)
    logger.info('worlds aligned')

    return [' '.join(words[idx] for idx in line) for line in lines]

def parse_args(argv=None):
    parser = ArgumentParser(description="Archive images or PDFs in the skill's data/archive directory and save their OCR transcripts alongside them.", allow_abbrev=False)
    parser.add_argument("input", nargs='+', help="Path to input image or PDF file")
    parser.add_argument('-v', '--verbose', action='store_true', help="log more info", default=False)
    parser.add_argument('-k', '--keep-on-place', action='store_true', help="Don't move the file, don't clean up", default=False)
    parser.add_argument('-p', '--protected', action='store_true', help='Do not replace an existing archived image')
    parser.add_argument('-s', '--silent', action='store_true', help="Don't send any callback", default=False)
    parser.add_argument('-sid', '--session-id', help="session id", default=None)
    parser.add_argument('-a', '--agent', help="Agent to notify", default="main")
    parser.add_argument('-w', '--wrapped', dest='wrap', action='store_true', help="OCR wrapped image", default=False)
    parser.add_argument('-stdout', '--stdout', action='store_true', help="send transcript text to stdout", default=False)
    # doctr not allow to set language, othercase:
    # parser.add_argument('-lang', '--language', help="Strict define language", default='')
    return parser.parse_args(argv)

def main(argv=None):
    for std in (sys.stdout, sys.stderr):  #repair for correct output
        if hasattr(std, "reconfigure"):
            std.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args(argv)
    if args.verbose:
        logger.setLevel(logging.INFO)

    logger.info(f'start main {vars(args)}')

    failed = False
    for filename in args.input:
        logger.info(f'start parse {filename}')
        try:
            processing(filename, **vars(args))
        except Exception as exc:
            logger.error('%s: %s', filename, exc)
            print(f'ERROR: {filename}: {exc}', file=sys.stderr)
            failed = True

    logger.info('stop')
    return 1 if failed else 0

def send_callback(message, silent=False, agent="main", session_id=None, **kwargs):
    # Notify the agent without making OCR depend on agent-turn completion.
    # A synchronous wait here made the launcher hit its timeout; the launcher
    # then retried the same image although OCR had not failed.
    if not silent:
        try:
            logger.info('before callback send')
            session_key = session_id if session_id and session_id.startswith("agent:") else f"agent:{agent}:main"
            event_name = message.partition("]")[0].lstrip("[") or "ocr"
            filename = message.rpartition("file:")[2].strip() or message
            params = json.dumps({ "key": session_key, "agentId": agent, "message": message, "idempotencyKey": f"{event_name}:{filename}", })
            kwargs = {
                "args": ["openclaw.cmd", "gateway", "call", "sessions.send", "--params", params, "--json"],
            }
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            process = subprocess.Popen(**kwargs, shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, )
            logger.info(f'callback dispatched {message} pid={process.pid}')
        except Exception as e:
            # Failure to send a notification must not break transcription.
            logger.error(f'callback dispatch failed: {e}')

def prepare_filename(filename, keep_on_place=False, **kwargs):
    if keep_on_place:
        return filename

    archive_dir = ARCHIVE_DIR
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    processed_filename = archive_dir / filename.name

    if filename.resolve() == processed_filename.resolve():
        return processed_filename
    shutil.move(filename, processed_filename)

    return processed_filename

def unwarp_image(filename):
    logger.info(f'before unwarp {filename}')
    model_path = settings.get('OCR_UNWARP_MODEL_PATH')
    unwarp = Unwarp(model_path=str(Path(model_path).expanduser())) if model_path else Unwarp()
    _image = Image.open(filename)
    image = unwarp.inference(_image)
    _image.close()
    image.save(filename.parent / f'{filename.stem}_unwarped{filename.suffix}')
    image.close()
    logger.info(f'unwarped {filename} save')
    return filename.parent / f'{filename.stem}_unwarped{filename.suffix}'


def process_file(filename, wrap=False, keep_on_place=False, **kwargs):
    logger.info(f'process_file {filename}')
    if filename.suffix.lower() == ".pdf":
        doc = DocumentFile.from_pdf(filename)
    else:
        if wrap:
            doc = DocumentFile.from_images(filename)
        else:
            unwarped_image = unwarp_image(filename)
            doc = DocumentFile.from_images(unwarped_image)
            if not keep_on_place:
                Path(unwarped_image).unlink(missing_ok=True)

    logger.info('Doctr doc created')
    # Run OCR
    model = get_model()
    result = model(doc)
    extract_info = result.export()

    logger.info('Doctr doc predicted')
    
    logger.info('predictions ready to align')

    transcript = filename.parent / f'{filename.stem}.txt'
    pages = []
    for page in extract_info['pages']:
        words = [ word for block in page['blocks'] for line in block['lines'] for word in line['words'] ]
        pages.append('\n'.join(align({'words': words})) if words else '')
    text = '\n\n'.join(pages)
    transcript.write_text(text, encoding='utf-8')

def get_model(size=MODEL_SIZE):
    os.environ['DOCTR_CACHE_DIR'] = str(ROOT / Path(settings.get('DOCTR_CACHE_DIR') or '.cache/doctr').expanduser())
    if not model.get(size):
        model[size] = ocr_predictor(pretrained=True, assume_straight_pages=False)
        logger.info('OCR model loaded')
    return model[size]

def finalize(filename, stdout=False, **kwargs):
    if stdout:
        transcript = (filename.parent / f'{filename.stem}.txt').read_text(encoding="utf-8")
        sys.stdout.write(transcript)


def processing(filename, **kwargs):

    # 1) prepare and check file
    logger.info(f'processing {filename}')
    in_path = Path(filename).expanduser().resolve()
    logger.info(f'processing full filename {in_path}')
    if not in_path.is_file():
        raise FileNotFoundError(f'Input not found: {in_path}')
    if in_path.suffix.lower() == '.txt':
        raise ValueError(f'Input must be an image or PDF, not a transcript: {in_path}')

    destination = in_path if kwargs.get('keep_on_place', False) else ARCHIVE_DIR / in_path.name
    if kwargs.get('protected') and destination.resolve() != in_path and destination.exists():
        raise FileExistsError(f'Archive destination already exists: {destination}')


    # 2) Notify caller about start of processing
    send_callback(f"[ocr-start] file: {in_path.name}", **kwargs)

    # 3) archivate file
    processed_filename = prepare_filename(in_path, **kwargs)
    processed_filename.with_suffix('.txt').unlink(missing_ok=True)

    # 4) transcribe    
    process_file(processed_filename, **kwargs)

    # 5) Notify agent via CLI so it can process the transcript
    send_callback(f"[ocr-done] file: {processed_filename.name}", **kwargs)

    finalize(processed_filename, **kwargs)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception as e:
        logger.error(f'{e}')
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)
