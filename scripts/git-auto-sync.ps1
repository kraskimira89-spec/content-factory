# Автосинхронизация каждые 30 минут (для Windows Task Scheduler)
# 1. git status --porcelain → если пусто, выход
# 2. Иначе: chore: автосинхронизация YYYY-MM-DD HH:mm

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
$msg = "автосинхронизация $now"
$scriptMain = "D:\git-entuziastov.ps1"
if (-not (Test-Path $scriptMain)) { $scriptMain = "D:\content-factory\scripts\git-sync.ps1" }

# Запуск в том же процессе — сохраняем Set-Location $projectPath
& $scriptMain -project $project -type chore -message $msg
