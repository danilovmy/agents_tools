# agents_tools

Tools for LLM agents. [Русская версия](README_RU.md)

## Xiaomi OCR: local test

`tests/codex/ocr.py` runs an image through `llama-mtmd-cli`, prints the text and timing statistics, and exits. No server is required.

The test requires Python 3, `llama-mtmd-cli` on `PATH`, and two model files:

- `D:\Downloads\Xiaomi-OCR-0.Q4_K_M.gguf`
- `D:\Downloads\Xiaomi-OCR-0.mmproj-bf16.gguf` — [vision module](https://huggingface.co/prithivMLmods/Xiaomi-OCR-0-GGUF/resolve/main/Xiaomi-OCR-0.mmproj-bf16.gguf)

The model paths are set at the beginning of the script. Run the example from the repository root in PowerShell:

```powershell
python tests\codex\ocr.py tests\codex\photo_2026-10-31_14-46-10.jpg
```

You can supply another image. The script reports total time, approximate model initialization time, and recognition time. To evaluate quality, pass a UTF-8 file containing the reference transcription:

```powershell
python tests\codex\ocr.py tests\codex\photo_2026-10-31_14-46-10.jpg --reference path\to\reference.txt
```

With a reference, the script reports character error rate (CER) and word error rate (WER). Quality cannot be measured without reference text.

## Xiaomi OCR skill setup

`skills/ocr-reader-xiaomi` uses Transformers and PyTorch and is independent of the test script above. It requires Python 3.12, the packages in `requirements.txt`, and the original Xiaomi-OCR-0 model in Safetensors format; it does not require `llama.cpp`.

Create an environment and install the dependencies from the repository root:

```powershell
python -m venv skills\ocr-reader-xiaomi\.venv
& skills\ocr-reader-xiaomi\.venv\Scripts\python.exe -m pip install -r skills\ocr-reader-xiaomi\requirements.txt
if (-not (Test-Path skills\ocr-reader-xiaomi\.env)) { Copy-Item skills\ocr-reader-xiaomi\.env.example skills\ocr-reader-xiaomi\.env }
```

Set `XIAOMI_OCR_MODEL_PATH` in `skills/ocr-reader-xiaomi/.env` to an absolute path to a local model directory, a path relative to the skill directory starting with `./` such as `./.cache/model`, or a Hugging Face model ID such as `xiaomi-research/Xiaomi-OCR-0`. A model ID causes the model to be downloaded on first use. Process environment variables take precedence over `.env`; the local `.env` is ignored by Git.

Windows with OpenClaw notifications is the default integration. Use `-s` with other agents or operating systems to disable OpenClaw notifications; compatible Python dependencies are still required. See the [skill instructions](skills/ocr-reader-xiaomi/SKILL.md) and [installed-skill test](skills/ocr-reader-xiaomi/test/README.md). The selected model is not ready for reliable recognition of Russian text; compare its output with the source.

By default, an image with the same name in the archive is replaced. Use `-p` / `--protected` to reject a collision. After the input is moved, an existing `.txt` is removed regardless of the flag, and the new result is written directly. If OCR fails before the write, the `.txt` will be absent; a write error can leave it incomplete. The archive is `skills/ocr-reader-xiaomi/data/archive`: it must be readable and writable, and moving the input requires permission to remove it from the source directory.

The transcript is saved to a text file. `--stdout` also prints it to standard output. Skill messages are written to `logger.log`, and errors are also printed to standard error. Python output is directed to standard error, but native libraries may write directly to standard output.

## docTR OCR skill setup

`skills/ocr-reader` uses docTR for recognition and docuwarp to flatten images. It requires Python 3.11 or newer. Install the dependencies from the repository root:

```powershell
python -m venv skills\ocr-reader\.venv
& skills\ocr-reader\.venv\Scripts\python.exe -m pip install -r skills\ocr-reader\requirements.txt
```

Windows with OpenClaw notifications is the default integration. Other agents can run the script with `-s` to disable notifications; add `--stdout` to print the transcript. The target system needs a compatible Python environment and dependencies. Actual OCR has been tested on Windows; other operating systems have not yet been tested. See [the skill instructions](skills/ocr-reader/SKILL.md) and [the installed-skill test](skills/ocr-reader/test/README.md).

By default, the docTR cache is `skills/ocr-reader/.cache/doctr`; model weights are stored in its `models` subdirectory and downloaded on first use if missing. Set `DOCTR_CACHE_DIR` in `skills/ocr-reader/.env` or the process environment to change it. Use an absolute path or a path relative to `skills/ocr-reader`, such as `.cache/doctr`. Process environment variables take precedence over `.env`; the local `.env` is ignored by Git. Variable references such as `${MODELS_DIR}` are not expanded in paths.

In `.env`, write Windows paths with backslashes unquoted or in single quotes, for example `DOCTR_CACHE_DIR='D:\Models\doctr'`. Inside double quotes, `python-dotenv` interprets sequences such as `\t` as special characters.

By default, docuwarp uses models from the installed package. The optional `OCR_UNWARP_MODEL_PATH` setting in `.env` or the environment can specify an absolute path to another `uvdoc.onnx` file; the auxiliary model remains in the package.

By default, an input with the same name in `skills/ocr-reader/data/archive` is replaced; `-p` / `--protected` rejects the replacement. Before OCR, after moving the input when needed, the old `.txt` is removed regardless of the flag, and the result is written directly. If OCR fails before writing, the `.txt` is absent; a write error can leave it incomplete. The archive must be readable and writable; moving the input also requires permission to remove it from the source directory.

The current default recognizer in docTR 1.1.0 does not include Cyrillic in its vocabulary. Language support depends on the model and installed dependency version.

The OCR skills have not yet been tested on Linux or macOS.
