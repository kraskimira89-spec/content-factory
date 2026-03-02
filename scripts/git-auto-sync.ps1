# Автосинхронизация каждые 30 минут (для Windows Task Scheduler)
# Вызывает основной скрипт — без дублирования логики.

param(
    [string]$project = "factory"
)

$now = Get-Date -Format "yyyy-MM-dd HH:mm"
$autoMessage = "автосинхронизация $now"

powershell -ExecutionPolicy Bypass -File "D:\content-factory\git-entuziastov.ps1" `
    -project $project `
    -type chore `
    -message $autoMessage
