---
name: ocr-reader-xiaomi
description: Extract text from images and PDFs with the local Xiaomi OCR model. Use when Xiaomi OCR or ocr-reader-xiaomi is requested.
---

# Xiaomi OCR reader

Use this skill to transcribe images or multi-page PDFs locally with Xiaomi-OCR-0, Transformers, and PyTorch. Windows with OpenClaw notifications is the default integration. Other agents and operating systems can use `-s` to disable OpenClaw notifications, provided compatible Python dependencies are installed. The selected model is not ready for reliable recognition of Russian text; verify results against the source.

## Setup

From the installed skill directory, create a Python 3.12 virtual environment, install the dependencies, and create `.env` from the example if it does not exist. Windows PowerShell:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Linux or macOS, with compatible dependencies:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
[ -f .env ] || cp .env.example .env
```

Use the environment's Python to run `ocr.py`. Set `XIAOMI_OCR_MODEL_PATH` in `.env` to a Hugging Face model ID, an absolute path to a local model directory, or a skill-relative path beginning with `./`, such as `./.cache/model`. Use the original Xiaomi-OCR-0 model in Safetensors format; GGUF is not supported. A model ID may download weights on first use. Process environment values override `.env`. For an installed-skill check, see [test/README.md](test/README.md).

## Run

Use absolute paths to the interpreter, `ocr.py`, and input. In Windows/OpenClaw mode, supply the agent and session ID:

```text
<skill-dir>/.venv/Scripts/python.exe <skill-dir>/ocr.py -a <agent> -sid <session_id> <absolute-input-path>
```

For other agents or a standalone run, use `-s` to disable callbacks. Add `-stdout` or `--stdout` to print the transcript:

```text
<venv-python> <skill-dir>/ocr.py -s --stdout <absolute-input-path>
```

Place flags before the list of input files. For normal processing omit `-k`; use it only to keep the input and transcript in place for debugging. The input is moved to `data/archive` in the skill directory. An existing same-named input is replaced by default; `-p` / `--protected` rejects a collision with another archived input. After preparing the input, an existing same-named `.txt` is removed regardless of `-p`, and a successful transcript is written directly. An error before writing leaves no transcript; a write error can leave it incomplete.

The image is passed without deskewing; PDFs are rendered and processed page by page. If the result says `Xiaomi OCR returned unknown response`, report that the image was not transcribed. Without `-s`, the script sends OpenClaw `[ocr-start]` and `[ocr-done]` callbacks asynchronously through `openclaw.cmd`. `-v` adds progress to `logger.log`; errors also go to stderr. Python output is redirected to stderr, but native libraries may write directly to stdout. The skill directory must be writable for the log, archive, and any local cache.

[Русская версия](SKILL_RU.md)
