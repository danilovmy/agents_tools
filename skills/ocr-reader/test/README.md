# Test the installed OCR skill

[Русский](#проверка-установленного-ocr-скилла)

Run these commands from the installed `ocr-reader` directory after installing the dependencies. Use a copy: the script moves its input into `data/archive` and may replace an existing file with the same name.

Windows PowerShell:

```powershell
Copy-Item .\test\test.jpg .\test\ocr-test.jpg
& .\.venv\Scripts\python.exe .\ocr.py -s --stdout (Resolve-Path .\test\ocr-test.jpg).Path
```

Linux or macOS, with compatible dependencies installed:

```sh
cp test/test.jpg test/ocr-test.jpg
.venv/bin/python ocr.py -s --stdout "$(pwd)/test/ocr-test.jpg"
```

`-s` disables OpenClaw notifications; `--stdout` prints the recognised text. The image and transcript are also saved as `data/archive/ocr-test.jpg` and `data/archive/ocr-test.txt`. The first run may download model weights. The OpenClaw integration targets Windows; the silent mode does not require OpenClaw. Actual OCR has been tested on Windows; other operating systems have not yet been tested.

# Проверка установленного OCR-скилла

Запускайте команды из папки установленного `ocr-reader` после установки зависимостей. Используется копия: скрипт перемещает исходный файл в `data/archive` и может заменить одноимённый файл в архиве.

Windows PowerShell:

```powershell
Copy-Item .\test\test.jpg .\test\ocr-test.jpg
& .\.venv\Scripts\python.exe .\ocr.py -s --stdout (Resolve-Path .\test\ocr-test.jpg).Path
```

Linux или macOS при установленных совместимых зависимостях:

```sh
cp test/test.jpg test/ocr-test.jpg
.venv/bin/python ocr.py -s --stdout "$(pwd)/test/ocr-test.jpg"
```

Флаг `-s` отключает уведомления OpenClaw, `--stdout` выводит распознанный текст. Изображение и текст также сохраняются в `data/archive/ocr-test.jpg` и `data/archive/ocr-test.txt`. При первом запуске могут загружаться веса моделей. Интеграция OpenClaw рассчитана на Windows; режим с `-s` не требует OpenClaw. Реальный запуск OCR проверен на Windows; другие ОС пока не проверялись.
