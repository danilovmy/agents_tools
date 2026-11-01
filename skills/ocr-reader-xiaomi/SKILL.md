---
name: ocr-reader-xiaomi
description: Extract text from images and PDFs with the local Xiaomi OCR model. Use when Xiaomi OCR or ocr-reader-xiaomi is requested.
---

# Xiaomi OCR reader

Extract text from images and multi-page PDFs with Xiaomi-OCR-0. Set up Python 3.12 and install `requirements.txt` in the skill directory. Configure `XIAOMI_OCR_MODEL_PATH` in the included `.env` or process environment. See [README.md](README.md) for setup and [test/README.md](test/README.md) for a post-install test.

Use absolute paths to the interpreter, script and input. For OpenClaw on Windows:

```text
<skill-dir>/.venv/Scripts/python.exe <skill-dir>/ocr.py -a <agent> -sid <session_id> <absolute-input-path>
```

For standalone use or other agents, disable callbacks with `-s`; add `--stdout` to print the transcript:

```text
<venv-python> <skill-dir>/ocr.py -s --stdout <absolute-input-path>
```

Place flags before input paths. The input is moved to `data/archive`, where its transcript is saved as `<stem>.txt`. An existing same-named input is replaced unless `-p` / `--protected` is set; use a copy if the original must be retained. Use `-k` only for debugging. An existing transcript is removed before OCR, even with `-p`; OCR failure can leave it absent or incomplete. The skill directory must be writable. If the output says `Xiaomi OCR returned unknown response`, report that the image was not transcribed. The model is not reliable for Russian text.
