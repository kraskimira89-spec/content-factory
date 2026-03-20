# Автонастройка PATH для CUDA и опциональная регистрация ежедневной задачи.
# Ищет последнюю установленную CUDA (v12.x/v13.x), добавляет bin/libnvvp в PATH (User или Machine),
# проверяет nvcc и может создать задачу в Планировщике Windows.
#
# Примеры:
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\cuda-path-auto.ps1"
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\cuda-path-auto.ps1" -Scope User -RegisterTask -TaskTime "09:10"
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\cuda-path-auto.ps1" -Scope Machine -RegisterTask

param(
    [ValidateSet("User", "Machine")]
    [string]$Scope = "User",
    [switch]$RegisterTask,
    [string]$TaskTime = "09:10"
)

$ErrorActionPreference = "Stop"

function Get-LatestCudaRoot {
    $base = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
    if (-not (Test-Path $base)) { return $null }

    $dirs = Get-ChildItem -Path $base -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "^v(12|13)\." }

    if (-not $dirs) { return $null }

    # Сортировка по номеру версии (v12.6 < v13.2 и т.д.)
    $latest = $dirs |
        Sort-Object { [version](($_.Name -replace "^v", "") + ".0") } -Descending |
        Select-Object -First 1
    return $latest.FullName
}

function Add-ToPathIfMissing {
    param(
        [string]$PathToAdd,
        [ValidateSet("User", "Machine")]
        [string]$Target
    )
    if (-not (Test-Path $PathToAdd)) { return $false }

    $current = [Environment]::GetEnvironmentVariable("Path", $Target)
    if ([string]::IsNullOrWhiteSpace($current)) {
        [Environment]::SetEnvironmentVariable("Path", $PathToAdd, $Target)
        return $true
    }

    $parts = $current.Split(";") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
    if ($parts -contains $PathToAdd) { return $false }

    $newPath = ($parts + $PathToAdd) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $newPath, $Target)
    return $true
}

function Register-CudaPathTask {
    param(
        [string]$ScriptPath,
        [string]$AtTime
    )

    $taskName = "CudaPathAutoUpdate"
    $factoryRoot = "D:\content-factory"
    $actionArgs = "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File `"$ScriptPath`" -Scope User"
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArgs -WorkingDirectory $factoryRoot
    $trigger = New-ScheduledTaskTrigger -Daily -At $AtTime
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    Write-Host "Task '$taskName' registered: daily at $AtTime." -ForegroundColor Green
}

try {
    $cudaRoot = Get-LatestCudaRoot
    if (-not $cudaRoot) {
        Write-Host "CUDA v12/v13 not found in 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA'." -ForegroundColor Yellow
        exit 1
    }

    $cudaBin = Join-Path $cudaRoot "bin"
    $cudaLibNvvp = Join-Path $cudaRoot "libnvvp"

    $addedBin = Add-ToPathIfMissing -PathToAdd $cudaBin -Target $Scope
    $addedNvvp = Add-ToPathIfMissing -PathToAdd $cudaLibNvvp -Target $Scope

    Write-Host "CUDA root: $cudaRoot" -ForegroundColor Cyan
    Write-Host "Scope: $Scope" -ForegroundColor Cyan
    if ($addedBin) { Write-Host "Added to PATH: $cudaBin" -ForegroundColor Green } else { Write-Host "Already in PATH: $cudaBin" -ForegroundColor DarkGray }
    if ($addedNvvp) { Write-Host "Added to PATH: $cudaLibNvvp" -ForegroundColor Green } else { Write-Host "Already in PATH: $cudaLibNvvp" -ForegroundColor DarkGray }

    # Обновим PATH текущего процесса, чтобы сразу попробовать nvcc
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

    $nvccCmd = Get-Command nvcc -ErrorAction SilentlyContinue
    if ($nvccCmd) {
        Write-Host "nvcc found: $($nvccCmd.Source)" -ForegroundColor Green
    } else {
        Write-Host "nvcc not found in current session. Reopen terminal and run: nvcc --version" -ForegroundColor Yellow
    }

    if ($RegisterTask) {
        $scriptPath = $MyInvocation.MyCommand.Path
        Register-CudaPathTask -ScriptPath $scriptPath -AtTime $TaskTime
        Write-Host "Check Task Scheduler: taskschd.msc" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
