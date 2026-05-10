# PDF2AI Converter Web UI 启动脚本
$venv = ".\venv\Scripts\python.exe"

if (Test-Path $venv) {
    & $venv server.py
} else {
    python server.py
}
