# Автонастройка PATH для CUDA и опциональная регистрация ежедневной задачи.
#
# Важно для onnxruntime-gpu / rembg: нужны DLL CUDA 12 (например cublasLt64_12.dll).
# Если установлены и v12.x и v13.x — по умолчанию выбирается ПОСЛЕДНЯЯ v12.x, а не v13.x.
#
# Примеры:
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\cuda-path-auto.ps1"
#   powershell -ExecutionPolicy Bypass -File "D:\content-factory\scripts\cuda-path-auto.ps1" -Scope User -RegisterTask -TaskTime "09:10"

param(
    [ValidateSet("User", "Machine")]
    [string]$Scope = "User",
    [switch]$RegisterTask,
    [string]$TaskTime = "09:10",
    # $true = сначала последняя CUDA 12.x (рекомендуется для rembg); $false = самая новая среди v12|v13
    [bool]$PreferCuda12 = $true
)

$ErrorActionPreference = "Stop"

function Get-CudaInstallRoots {
    $base = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
    if (-not (Test-Path $base)) { return @() }
    return @(Get-ChildItem -Path $base -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "^v(12|13)\." })
}

function Get-SelectedCudaRoot {
    param(
        [array]$Dirs,
        [bool]$Prefer12
    )
    if (-not $Dirs -or $Dirs.Count -eq 0) { return $null }

    $v12 = $Dirs | Where-Object { $_.Name -match "^v12\." }
    $v13 = $Dirs | Where-Object { $_.Name -match "^v13\." }

    if ($Prefer12 -and $v12) {
        return ($v12 | Sort-Object { [version](($_.Name -replace "^v", "") + ".0") } -Descending | Select-Object -First 1).FullName
    }
    # Иначе — максимальная версия среди всех найденных
    return ($Dirs | Sort-Object { [version](($_.Name -replace "^v", "") + ".0") } -Descending | Select-Object -First 1).FullName
}

function Set-CudaPathPriority {
    param(
        [string]$CudaRoot,
        [ValidateSet("User", "Machine")]
        [string]$Target
    )

    $cudaBin = Join-Path $CudaRoot "bin"
    $cudaLibNvvp = Join-Path $CudaRoot "libnvvp"
    if (-not (Test-Path $cudaBin)) {
        throw "CUDA bin not found: $cudaBin"
    }

    $current = [Environment]::GetEnvironmentVariable("Path", $Target)
    $parts = @()
    if (-not [string]::IsNullOrWhiteSpace($current)) {
        $parts = $current.Split(";") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
    }

    # Убрать записи ...\CUDA\vX.Y\bin и ...\CUDA\vX.Y\libnvvp (любая версия)
    $filtered = $parts | Where-Object {
        $p = $_
        $isCudaBin = $p -match '\\NVIDIA GPU Computing Toolkit\\CUDA\\v[\d.]+\\bin$'
        $isCudaLib = $p -match '\\NVIDIA GPU Computing Toolkit\\CUDA\\v[\d.]+\\libnvvp$'
        -not ($isCudaBin -or $isCudaLib)
    }

    $prepend = @($cudaBin)
    if (Test-Path $cudaLibNvvp) { $prepend += $cudaLibNvvp }

    $newPath = ($prepend + $filtered) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $newPath, $Target)
    [Environment]::SetEnvironmentVariable("CUDA_PATH", $CudaRoot, $Target)

    return @{ Bin = $cudaBin; LibNvvp = $cudaLibNvvp; RemovedCount = ($parts.Count - $filtered.Count) }
}

function Register-CudaPathTask {
    param(
        [string]$ScriptPath,
        [string]$AtTime
    )

    $taskName = "CudaPathAutoUpdate"
    $factoryRoot = "D:\content-factory"
    $actionArgs = "-ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -File `"$ScriptPath`" -Scope User -PreferCuda12:`$true"
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArgs -WorkingDirectory $factoryRoot
    $trigger = New-ScheduledTaskTrigger -Daily -At $AtTime
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
    Write-Host "Task '$taskName' registered: daily at $AtTime (PreferCuda12)." -ForegroundColor Green
}

try {
    $dirs = Get-CudaInstallRoots
    $cudaRoot = Get-SelectedCudaRoot -Dirs $dirs -Prefer12:$PreferCuda12
    if (-not $cudaRoot) {
        Write-Host "CUDA v12/v13 not found in 'C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA'." -ForegroundColor Yellow
        exit 1
    }

    $info = Set-CudaPathPriority -CudaRoot $cudaRoot -Target $Scope

    Write-Host "CUDA root (selected): $cudaRoot" -ForegroundColor Cyan
    Write-Host "Scope: $Scope | PreferCuda12: $PreferCuda12" -ForegroundColor Cyan
    Write-Host "Prepended: $($info.Bin)" -ForegroundColor Green
    if (Test-Path $info.LibNvvp) { Write-Host "Prepended: $($info.LibNvvp)" -ForegroundColor Green }
    Write-Host "Removed old CUDA PATH entries: $($info.RemovedCount)" -ForegroundColor DarkGray

    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    $env:CUDA_PATH = $cudaRoot

    $nvccCmd = Get-Command nvcc -ErrorAction SilentlyContinue
    if ($nvccCmd) {
        Write-Host "nvcc found: $($nvccCmd.Source)" -ForegroundColor Green
    } else {
        Write-Host "nvcc not found in this session. Open a NEW terminal." -ForegroundColor Yellow
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
