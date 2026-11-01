# OCR reader

[Русский](README_RU.md)

Extract text from images and multi-page PDFs using docTR. Images are straightened with docuwarp before recognition. Windows with OpenClaw notifications is the default integration. Other agents and operating systems can use `-s` to disable notifications, provided compatible Python dependencies are installed. Actual OCR has been tested on Windows; other operating systems have not yet been tested.

## Installation

Install the `ocr-reader` directory where your agent loads skills. From that directory, create a Python 3.11+ environment and install the dependencies:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On Linux or macOS use `.venv/bin/python` instead. The first run may download model weights. The skill directory must be writable for the log, cache and archive.

## Usage

For OpenClaw on Windows, use the command in [SKILL.md](SKILL.md) with the agent and session ID. For a standalone run or another agent, pass `-s`; add `--stdout` to print the transcript. See [test/README.md](test/README.md) for a complete post-install test.

The script moves its input to `data/archive` and stores the transcript alongside it. It replaces an existing same-named input unless `-p` / `--protected` is set. Use a copy if the original should remain in place. The `-k` flag is reserved for debugging.

Configure `DOCTR_CACHE_DIR` and optional `OCR_UNWARP_MODEL_PATH` in `.env` or the process environment. The environment takes precedence. The cache path can be absolute or relative to the skill directory; use an absolute unwarp model path. Variable references such as `${MODELS_DIR}` are not expanded.

The default docTR 1.1.0 recognition model does not support Cyrillic and is not suitable for Russian text. Language support depends on the model and installed version.
