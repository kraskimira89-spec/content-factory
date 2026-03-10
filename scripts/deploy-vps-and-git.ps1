# Деплой темы на VPS + коммит и пуш в GitHub
# Выполняет: 1) копирование файлов темы на VPS  2) git add/commit/push для entuziastov75-vps
#
# Запуск:
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\deploy-vps-and-git.ps1"
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\deploy-vps-and-git.ps1" -message "сортировка по колонке Статус"
#
# Параметры:
#   -message "описание"  — описание коммита (по умолчанию: деплой темы на VPS)

param(
    [string]$message = "деплой темы на VPS",
    [string]$type = "feat"
)

$ErrorActionPreference = "Stop"
$factoryPath = "D:\content-factory"
$vpsPath = "D:\entuziastov75-vps"
if (-not (Test-Path $vpsPath) -and (Test-Path "C:\Users\user\Documents\seo_entuziastov75")) {
    $vpsPath = "C:\Users\user\Documents\seo_entuziastov75"
}

# 1. Deploy to VPS
Write-Host "=== Step 1: Deploy theme to VPS ===" -ForegroundColor Cyan
Set-Location $factoryPath
$deployResult = python scripts/deploy_to_vps.py --mode theme 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Deploy failed. Exit." -ForegroundColor Red
    Write-Host $deployResult
    exit 1
}
Write-Host $deployResult

# 2. Git for vps
Write-Host ""
Write-Host "=== Step 2: Git commit and push entuziastov75-vps ===" -ForegroundColor Cyan
if (-not (Test-Path $vpsPath)) {
    Write-Host "Error: folder not found: $vpsPath" -ForegroundColor Red
    exit 1
}

$status = git -C $vpsPath status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "No changes in vps to commit. Deploy done." -ForegroundColor Yellow
    exit 0
}

$commitMessage = "${type}: $message"
Write-Host "Commit: $commitMessage"
git -C $vpsPath add .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: git add failed." -ForegroundColor Red
    exit 1
}

git -C $vpsPath commit -m "$commitMessage"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: git commit failed." -ForegroundColor Red
    exit 1
}

git -C $vpsPath push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: git push failed. Check network or git pull." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Done: VPS updated, pushed to GitHub." -ForegroundColor Green
