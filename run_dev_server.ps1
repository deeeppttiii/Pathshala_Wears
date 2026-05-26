$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$project = Join-Path $root "shopping_assistant"
$python = Join-Path $root ".venv\Scripts\python.exe"
$logDir = $root
$outLog = Join-Path $logDir "runserver.out.log"
$errLog = Join-Path $logDir "runserver.err.log"

Set-Location $project

Write-Host "Pathshala Wear development server watchdog" -ForegroundColor Green
Write-Host "URL: http://127.0.0.1:8000/" -ForegroundColor Cyan
Write-Host "Keep this window open. If Django exits, it will restart automatically." -ForegroundColor Yellow
Write-Host ""

while ($true) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $outLog -Value "[$timestamp] Starting Django development server..."
    Write-Host "[$timestamp] Starting Django development server..." -ForegroundColor Green

    & $python manage.py runserver 127.0.0.1:8000 --noreload 1>> $outLog 2>> $errLog

    $exitCode = $LASTEXITCODE
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $errLog -Value "[$timestamp] Django server exited with code $exitCode. Restarting in 3 seconds..."
    Write-Host "[$timestamp] Django server exited with code $exitCode. Restarting in 3 seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
}
