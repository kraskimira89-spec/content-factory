# Регистрация задач в Планировщике Windows: автосинхронизация с GitHub для обеих папок.
# Запустить один раз с правами пользователя.
#
# Запуск:
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\register-git-sync-tasks.ps1"
#
# Создаёт две задачи:
#   - GitSyncContentFactory — каждые 30 мин (content-factory)
#   - GitSyncEntuziastov75Vps — каждые 30 мин (entuziastov75-vps / seo_entuziastov75)

$factoryRoot = "D:\content-factory"
$syncScript = Join-Path $factoryRoot "scripts\git-auto-sync.ps1"
$gitScript = Join-Path $factoryRoot "git-entuziastov.ps1"

if (-not (Test-Path $syncScript)) {
    Write-Host "Error: $syncScript not found." -ForegroundColor Red
    exit 1
}

$tasks = @(
    @{
        Name = "GitSyncContentFactory"
        Project = "factory"
    },
    @{
        Name = "GitSyncEntuziastov75Vps"
        Project = "vps"
    }
)

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 365)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

foreach ($t in $tasks) {
    $actionArgs = "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File `"$syncScript`" -project $($t.Project)"
    $actionObj = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArgs -WorkingDirectory $factoryRoot
    try {
        Register-ScheduledTask -TaskName $t.Name -Action $actionObj -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
        Write-Host "Task '$($t.Name)' registered (project: $($t.Project))." -ForegroundColor Green
    } catch {
        Write-Host "Error registering $($t.Name): $_" -ForegroundColor Red
    }
}

Write-Host "`nDone. Check: taskschd.msc" -ForegroundColor Cyan
Write-Host "To run manually: powershell -ExecutionPolicy Bypass -File `"$syncScript`" -project factory" -ForegroundColor Gray
