# Автосинхронизация каждые 30 минут (для Windows Task Scheduler)
# Вызывает основной скрипт — без дублирования логики.

param(
    [string]$project = "factory"
)

$factoryPath = "D:\content-factory"
$vpsPath = "D:\entuziastov75-vps"
if (-not (Test-Path $vpsPath) -and (Test-Path "C:\Users\user\Documents\seo_entuziastov75")) {
    $vpsPath = "C:\Users\user\Documents\seo_entuziastov75"
}

$projectPath = if ($project -eq "vps") { $vpsPath } else { $factoryPath }
if (-not (Test-Path $projectPath)) { exit 0 }

Set-Location $projectPath
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) { exit 0 }

$now = Get-Date -Format "yyyy-MM-dd HH:mm"
$autoMessage = "автосинхронизация $now"

powershell -ExecutionPolicy Bypass -File "D:\content-factory\git-entuziastov.ps1" `
    -project $project `
    -type chore `
    -message $autoMessage
