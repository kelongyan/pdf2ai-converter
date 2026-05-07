# PDF to Markdown Tool Launcher
# PowerShell Script

# Set console encoding to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Change to script directory
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   PDF to Markdown Tool Starting..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check virtual environment
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "[Error] Virtual environment not found" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check dependencies
Write-Host "Checking dependencies..." -ForegroundColor Yellow
& "venv\Scripts\python.exe" -c "import rich, inquirer" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    & "venv\Scripts\pip.exe" install rich inquirer -q
    Write-Host "Dependencies installed" -ForegroundColor Green
    Write-Host ""
}

# Run launcher
Write-Host "Starting interactive interface..." -ForegroundColor Green
Write-Host ""

& "venv\Scripts\python.exe" launcher.py

Write-Host ""
Write-Host "Program exited" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to close"
