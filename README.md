# agents_tools

Tools for LLM agents. [Русская версия](README_RU.md)

## OCR skills

Each skill contains installation and usage instructions in English and Russian, as well as a post-install test:

- [Xiaomi OCR](skills/ocr-reader-xiaomi/README.md) — local image and PDF transcription using Xiaomi-OCR-0. [Test](skills/ocr-reader-xiaomi/test/README.md).
- [docTR OCR](skills/ocr-reader/README.md) — image and PDF transcription using docTR, with docuwarp image correction. [Test](skills/ocr-reader/test/README.md).

Both skills use their own Python environment and `.env` file. Their default integration is Windows with OpenClaw; use `-s` for standalone operation or other agents. The first run may download model weights. Actual OCR on Linux and macOS has not been verified.

The scripts move input files into the skill's `data/archive` directory and save the recognized text there. Use a copy if the original must remain in place. See each skill's instructions for options, model configuration, language support, and archive behavior.
