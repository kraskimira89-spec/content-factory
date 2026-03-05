# Запуск цепочки агентов с кодировкой UTF-8 (без кракозябр в терминале)
$OutputEncoding = [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"
Set-Location $PSScriptRoot
& .\venv\Scripts\Activate.ps1 2>$null
if (-not $?) { & .\venv\Scripts\activate.bat 2>$null }
& cmd /c "run_agents.bat"
