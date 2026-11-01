# Test the installed Xiaomi OCR skill

[Русский](#проверка-установленного-xiaomi-ocr)

Run these commands from the installed `ocr-reader-xiaomi` directory after installing the dependencies. If `.env` does not exist, copy `.env.example` to `.env` and configure `XIAOMI_OCR_MODEL_PATH`. The example uses the Hugging Face model ID, which downloads the model on first use; alternatively, set an absolute path to a local Safetensors model directory or a skill-relative path such as `./.cache/model`. An existing `.env` does not need to be replaced. A local model can be used offline when all required files and dependencies are already present.

The sample is copied to a temporary location because OCR moves its input into `data/archive`. The randomly generated name and `-p` protect existing archived inputs.

Windows PowerShell:

```powershell
$sampleName = 'xiaomi-ocr-' + [guid]::NewGuid().ToString('N') + '.jpg'
$samplePath = Join-Path ([System.IO.Path]::GetTempPath()) $sampleName
Copy-Item -LiteralPath .\test\test.jpg -Destination $samplePath
& .\.venv\Scripts\python.exe .\ocr.py -s -p --stdout $samplePath
```

Linux or macOS, with compatible dependencies installed:

```sh
workdir="$(mktemp -d "${TMPDIR:-/tmp}/xiaomi-ocr.XXXXXX")"
sample="$workdir/$(basename "$workdir").jpg"
cp test/test.jpg "$sample"
.venv/bin/python ocr.py -s -p --stdout "$sample"
```

`-s` disables OpenClaw notifications, and `--stdout` prints the transcript. The input image and a same-named `.txt` are also saved in `data/archive`. Compare the result with the image: the suggested model is not ready for reliable Russian-language OCR. Windows with OpenClaw is the default integration; `-s` does not require OpenClaw and can be used with other agents and operating systems when compatible Python dependencies are available.

# Проверка установленного Xiaomi OCR

Запускайте команды из папки установленного `ocr-reader-xiaomi` после установки зависимостей. Если `.env` отсутствует, скопируйте `.env.example` в `.env` и настройте `XIAOMI_OCR_MODEL_PATH`. В примере указан ID модели Hugging Face: при первом использовании модель будет скачана. Также можно указать абсолютный путь к локальной папке модели Safetensors или путь от папки скилла, например `./.cache/model`. Существующий `.env` заменять не требуется. Локальная модель работает без сети, если все её файлы и зависимости уже доступны.

Образец копируется во временную папку, так как OCR переносит исходный файл в `data/archive`. Случайное имя и `-p` защищают существующие архивные файлы.

Windows PowerShell:

```powershell
$sampleName = 'xiaomi-ocr-' + [guid]::NewGuid().ToString('N') + '.jpg'
$samplePath = Join-Path ([System.IO.Path]::GetTempPath()) $sampleName
Copy-Item -LiteralPath .\test\test.jpg -Destination $samplePath
& .\.venv\Scripts\python.exe .\ocr.py -s -p --stdout $samplePath
```

Linux или macOS при установленных совместимых зависимостях:

```sh
workdir="$(mktemp -d "${TMPDIR:-/tmp}/xiaomi-ocr.XXXXXX")"
sample="$workdir/$(basename "$workdir").jpg"
cp test/test.jpg "$sample"
.venv/bin/python ocr.py -s -p --stdout "$sample"
```

Флаг `-s` отключает уведомления OpenClaw, `--stdout` выводит распознанный текст. Изображение и одноимённый `.txt` также сохраняются в `data/archive`. Сверьте результат с изображением: предложенная модель пока не готова к надёжному распознаванию русских текстов. Интеграция по умолчанию рассчитана на Windows и OpenClaw; `-s` не требует OpenClaw и подходит другим агентам и операционным системам при наличии совместимых Python-зависимостей.
