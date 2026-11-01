"""Run Xiaomi OCR locally and hand transcripts to the OCR reader pipeline."""

import argparse
import contextlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from functools import cache
from pathlib import Path

import pypdfium2 as pdfium
from dotenv import dotenv_values
from PIL import Image

ROOT = Path(__file__).resolve().parent
settings = {**dotenv_values(ROOT / ".env", interpolate=False, encoding="utf-8-sig"), **os.environ}
ARCHIVE = ROOT / "data" / "archive"
PROMPT = (
    "Extract all information from the document image and represent it in markdown format. "
    "Preserve every line and include the header and footer. Organize the text in reading order. "
    "Transcribe numbers and text exactly as printed."
)
MAX_TOKENS = 4096
IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"})
INPUT_EXTENSIONS = IMAGE_EXTENSIONS | {".pdf"}
logger = logging.getLogger(__name__)
handler = logging.FileHandler(ROOT / "logger.log", encoding="utf-8")
handler.setFormatter(logging.Formatter("%(asctime)s: %(message)s"))
logger.addHandler(handler)


def parse_args(argv=None, output=None):
    parser = argparse.ArgumentParser(description="Archive files and transcribe them with local Xiaomi OCR.", allow_abbrev=False)
    parser.add_argument("input", nargs="+", help="Input PDF or images: JPG, JPEG, PNG, WEBP, BMP, TIF or TIFF")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed progress")
    parser.add_argument("-k", "--keep-on-place", action="store_true", help="Keep input in place")
    parser.add_argument("-p", "--protected", action="store_true", help="Do not replace an existing archived input")
    parser.add_argument("-s", "--silent", action="store_true", help="Do not send callbacks")
    parser.add_argument("-sid", "--session-id", default=None, help="Agent session ID")
    parser.add_argument("-a", "--agent", default="main", help="Agent to notify")
    parser.add_argument("-stdout", "--stdout", action="store_true", help="Print the transcript")
    with contextlib.redirect_stdout(output or sys.stdout):
        return parser.parse_args(argv)


def send_callback(message, args):
    if args.silent:
        return
    session_key = args.session_id if args.session_id and args.session_id.startswith("agent:") else f"agent:{args.agent}:main"
    event_name = message.partition("]")[0].lstrip("[") or "ocr"
    filename = message.rpartition("file:")[2].strip() or message
    params = json.dumps({"key": session_key, "agentId": args.agent, "message": message,
                         "idempotencyKey": f"{event_name}:{filename}"}, ensure_ascii=False)
    options = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL,
               "stderr": subprocess.DEVNULL, "shell": False}
    if sys.platform == "win32":
        options["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        subprocess.Popen(["openclaw.cmd", "gateway", "call", "sessions.send", "--params", params, "--json"], **options)
    except OSError as exc:
        logger.warning("Callback could not be dispatched: %s", exc)


@cache
def get_inference():
    """Load the model lazily once and reuse it for every image in this process."""
    model_path = (settings.get("XIAOMI_OCR_MODEL_PATH") or "").strip()
    if not model_path:
        raise ValueError("Missing model: set XIAOMI_OCR_MODEL_PATH in .env or the environment")
    if model_path.startswith(("./", ".\\")):
        model_path = str((ROOT / model_path).resolve())

    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float32 if device == "cpu" else torch.float16
    logger.info("Loading Xiaomi OCR model %s on %s", model_path, device)
    processor = AutoProcessor.from_pretrained(model_path)
    model = AutoModelForImageTextToText.from_pretrained(model_path, dtype=dtype).to(device).eval()
    return torch, processor, model, device


def run_xiaomi(image):
    torch, processor, model, device = get_inference()

    # Transformers otherwise rotates images according to EXIF orientation.
    # Give it a copy with the original pixel orientation and no EXIF data.
    image_source = contextlib.nullcontext(image) if isinstance(image, Image.Image) else Image.open(image)
    with image_source as original:
        with original.convert("RGB") as prepared:
            prepared.info.pop("exif", None)
            messages = [{"role": "user", "content": [ {"type": "image", "image": prepared}, {"type": "text", "text": PROMPT}, ]}]
            inputs = processor.apply_chat_template( messages, tokenize=True, add_generation_prompt=True, return_dict=True, return_tensors="pt", ).to(device)
    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=MAX_TOKENS, do_sample=False)
    new_tokens = output[:, inputs["input_ids"].shape[1]:]
    if new_tokens.shape[1] >= MAX_TOKENS:
        eos = model.generation_config.eos_token_id
        eos_ids = {eos} if isinstance(eos, int) else set(eos or ())
        if new_tokens[0, -1].item() not in eos_ids:
            raise RuntimeError(f"Xiaomi OCR reached the {MAX_TOKENS}-token limit; transcript may be incomplete")
    text = processor.batch_decode(new_tokens, skip_special_tokens=True)[0].replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"^(?:<think>\s*)?</think>\s*", "", text, count=1).strip()
    logger.info("Recognized %s", image)
    return text or f"Xiaomi OCR returned unknown response for {image}"


def transcribe_pdf(path):
    texts = []
    with pdfium.PdfDocument(str(path)) as document:
        for index in range(len(document)):
            logger.info("Processing PDF page %d/%d", index + 1, len(document))
            with contextlib.closing(document[index]) as page, contextlib.closing(page.render(scale=150 / 72)) as bitmap, contextlib.closing(bitmap.to_pil()) as image:
                texts.append(run_xiaomi(image))
    if not texts:
        logger.info(f"PDF has no info: {path}")
    return "\n\n".join(texts)


def processing(filename, args, output=None):
    source = Path(filename).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(f"Input not found: {source}")
    if source.suffix.lower() not in INPUT_EXTENSIONS:
        raise ValueError(f"Unsupported format: {source.suffix or '(none)'}; use PDF, JPG, JPEG, PNG, WEBP, BMP, TIF or TIFF")
    destination = source if args.keep_on_place else ARCHIVE / source.name
    same_file = destination.resolve() == source
    if args.protected and not same_file and destination.exists():
        raise FileExistsError(f"Archive destination already exists: {destination}")
    transcript = destination.with_suffix(".txt")
    send_callback(f"[ocr-start] file: {source.name}", args)
    if not same_file:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source, destination)
    transcript.unlink(missing_ok=True)
    logger.info("Processing %s", destination)
    if destination.suffix.lower() == ".pdf":
        text = transcribe_pdf(destination)
    else:
        text = run_xiaomi(destination)
    transcript.write_text(text, encoding="utf-8", newline="\n")
    send_callback(f"[ocr-done] file: {destination.name}", args)
    logger.info("Saved transcript: %s", transcript)
    if args.stdout:
        print(text, file=output, flush=True)
    return transcript


def main(argv=None, output=None):
    # Callers invoking main() directly are responsible for managing stdout.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = parse_args(argv, output)
    if args.verbose:
        logger.setLevel(logging.INFO)
    failed = False
    for filename in args.input:
        try:
            processing(filename, args, output)
        except Exception as exc:
            logger.error("%s: %s", filename, exc)
            print(f"ERROR: {filename}: {exc}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    output = sys.stdout
    try:
        # Native code can bypass this Python redirect and write to stdout.
        with contextlib.redirect_stdout(sys.stderr):
            raise SystemExit(main(output=output))
    except Exception as exc:
        logger.error("%s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
