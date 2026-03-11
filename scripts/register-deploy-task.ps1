# Регистрация задачи в Планировщике Windows: автоматический деплой темы на VPS.
# Запустить один раз с правами пользователя (не требуются права администратора).
#
# Запуск:
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\register-deploy-task.ps1"
#
# После регистрации задача "DeployThemeToVPS" будет выполняться по расписанию.
# Расписание по умолчанию: ежедневно в 09:00. Можно изменить ниже ($schedule).

param(
    [string]$Schedule = "daily"  # daily | hourly | atlogon
)

$taskName = "DeployThemeToVPS"
$factoryRoot = "D:\content-factory"
$scriptPath = Join-Path $factoryRoot "scripts\deploy-theme-only.ps1"
$action = "powershell.exe"
$actionArgs = "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File `"$scriptPath`""

# Триггер по расписанию
if ($Schedule -eq "hourly") {
    $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 365)
} elseif ($Schedule -eq "atlogon") {
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
} else {
    # daily at 09:00
    $trigger = New-ScheduledTaskTrigger -Daily -At "09:00"
}

$actionObj = New-ScheduledTaskAction -Execute $action -Argument $actionArgs -WorkingDirectory $factoryRoot
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

try {
    Register-ScheduledTask -TaskName $taskName -Action $actionObj -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    Write-Host "Задача '$taskName' зарегистрирована в Планировщике Windows." -ForegroundColor Green
    Write-Host "Расписание: $Schedule (при $Schedule = daily — ежедневно в 09:00)." -ForegroundColor Cyan
    Write-Host "Проверить: Планировщик заданий (taskschd.msc) -> Библиотека -> $taskName" -ForegroundColor Gray
} catch {
    Write-Host "Ошибка регистрации задачи: $_" -ForegroundColor Red
    exit 1
}
