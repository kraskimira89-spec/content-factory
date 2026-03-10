# Деплой темы на VPS → локальный коммит → пуш в GitHub
# Порядок: 1) изменения попадают на сайт, 2) сохраняются в репо, 3) отправляются в GitHub
#
# Запуск:
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\deploy-theme-then-git.ps1"
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\deploy-theme-then-git.ps1" -message "кнопка Заказать звонок и высота Hero"
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\deploy-theme-then-git.ps1" -type fix -message "лендинг конференц-зала"

param(
    [string]$type = "feat",
    [string]$message = "деплой темы на VPS"
)

$ErrorActionPreference = "Stop"
$factoryRoot = "D:\content-factory"

# 1. Деплой темы на VPS (чтобы изменения сразу действовали на сайте)
Write-Host "=== 1. Деплой темы на VPS ===" -ForegroundColor Cyan
Push-Location $factoryRoot
try {
    python scripts/deploy_to_vps.py --mode theme
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Деплой завершился с ошибкой. Остановка." -ForegroundColor Red
        exit 1
    }
} finally {
    Pop-Location
}

# 2. Локальный коммит и пуш в GitHub (vps = seo_entuziastov75)
Write-Host "`n=== 2. Коммит и отправка в GitHub (vps) ===" -ForegroundColor Cyan
& (Join-Path $factoryRoot "git-entuziastov.ps1") -project vps -type $type -message $message
if ($LASTEXITCODE -ne 0) {
    Write-Host "Git-синхронизация завершилась с ошибкой." -ForegroundColor Red
    exit 1
}

Write-Host "`nГотово: сайт на VPS обновлён, изменения в GitHub." -ForegroundColor Green
