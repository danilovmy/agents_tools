---
name: ocr-reader
description: Extract text from images and PDFs using local docTR OCR. Use for photographed or scanned documents, including multi-page PDFs.
---

# OCR reader

Use this skill to extract text from an image or PDF. Windows with OpenClaw notifications is the default integration. For other agents and operating systems, use `-s` to disable OpenClaw notifications; the required Python dependencies must be available on the target system. Actual OCR has been tested on Windows; other operating systems have not yet been tested.

## Setup

Create a virtual environment in the skill directory and install `requirements.txt` into it. On Windows, from the skill directory:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Use that environment's Python to run `ocr.py`, rather than assuming the system Python has the dependencies. On Unix-like systems, the environment's interpreter is `.venv/bin/python`. Models may be downloaded on first use. For an installed-skill check, see [test/README.md](test/README.md).

## Run

Use absolute paths to the interpreter, `ocr.py`, and input file. In Windows/OpenClaw mode, supply the agent and session ID:

```text
<skill-dir>/.venv/Scripts/python.exe <skill-dir>/ocr.py -a <agent> -sid <session_id> <absolute-input-path>
```

For other agents or a standalone run, disable callbacks with `-s`. Add `--stdout` when the calling agent needs the transcript in the command output:

```text
<venv-python> <skill-dir>/ocr.py -s --stdout <absolute-input-path>
```

For normal processing, omit `-k` / `--keep-on-place`, including when the input is already in the archive. Only use `-k` for explicit debugging when the intermediate `<stem>_unwarped.<ext>` file must be retained.

The input is moved into `data/archive` in the skill directory and the transcript is saved there as `<stem>.txt`. A same-named archived input is replaced by default. Use `-p` / `--protected` to reject a collision with another archived input; this flag does not prevent processing an input already in the archive or using `-k`. After the image or PDF is prepared, an existing same-named transcript is removed regardless of `--protected`. A successful OCR writes the new transcript directly. If OCR fails before writing, the transcript is absent; a write error can leave it incomplete.

## Paths and settings

The skill directory must be writable for `logger.log`, the archive, and the default model cache. Configure `DOCTR_CACHE_DIR` and optional `OCR_UNWARP_MODEL_PATH` in the skill's `.env` or the process environment; process environment values take precedence. `DOCTR_CACHE_DIR` can be absolute or relative to the skill directory. Use an absolute path for `OCR_UNWARP_MODEL_PATH`. The default docTR cache is `.cache/doctr` in the skill directory. Variable references such as `${MODELS_DIR}` are not expanded.

The default docTR 1.1.0 recognizer does not include Cyrillic in its vocabulary. Support for particular languages depends on the model and installed dependency version.
