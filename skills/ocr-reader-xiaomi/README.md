# Xiaomi OCR reader

[Русский](README_RU.md)

Extract text from images and multi-page PDFs locally with Xiaomi-OCR-0, Transformers and PyTorch. Images are not deskewed; PDFs are processed page by page. Windows with OpenClaw notifications is the default integration. Other agents and operating systems can use `-s` to disable notifications, provided compatible Python dependencies are installed. Linux and macOS have not yet been tested.

## Installation

Place the complete `ocr-reader-xiaomi` directory, including its `.env` file, where your agent loads skills. From that directory, create a Python 3.12 environment and install the dependencies:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On Linux or macOS, use `python3.12 -m venv .venv` and `.venv/bin/python` for installation and execution. Compatible dependencies are required.

The included `.env` selects `xiaomi-research/Xiaomi-OCR-0`. On first use Transformers downloads the model by this ID into its own cache. You can instead set `XIAOMI_OCR_MODEL_PATH` to an absolute path to a local model directory or a path starting with `./` relative to the skill directory, such as `./.cache/model`. The original model in Transformers/Safetensors format is required; GGUF is not supported. The process environment takes precedence over `.env`. Local offline use requires the complete model and dependencies to be available already.

The skill directory must be writable for the log and archive, and for any local model cache. See [test/README.md](test/README.md) for a complete post-install test.

## Usage

For OpenClaw on Windows, use the command in [SKILL.md](SKILL.md) with the agent and session ID. For a standalone run or another agent, pass `-s` to disable callbacks; add `--stdout` to print the transcript. Use the virtual environment's Python, absolute input paths, and put flags before the input files. For example, from the skill directory in PowerShell:

```powershell
& .\.venv\Scripts\python.exe .\ocr.py -s --stdout 'C:\path\to\image.jpg'
```

Supported inputs are PDF, JPG, JPEG, PNG, WEBP, BMP, TIF and TIFF. The script moves each input to `data/archive` and saves a same-stem `.txt` beside it. It replaces an existing same-named input unless `-p` / `--protected` is set. Use a copy if the original should remain in place. `-k` keeps the input and transcript in place for debugging.

An existing transcript is removed before OCR regardless of `-p`; if recognition fails before writing, it is absent, and a write error can leave it incomplete. The archive must be readable and writable, and moving the input requires permission to remove it from its original directory. Messages are written to `logger.log`, errors also go to stderr. Native libraries may write directly to stdout.

The selected model is not ready for reliable recognition of Russian text; compare results with the source. If the output says `Xiaomi OCR returned unknown response`, the image was not transcribed.
