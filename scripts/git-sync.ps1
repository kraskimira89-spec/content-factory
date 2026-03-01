# Полу-автоматическая синхронизация content-factory и entuziastov75-vps с GitHub
# Запуск: powershell -ExecutionPolicy Bypass -File "D:\git-entuziastov.ps1" [-project factory|vps]

param(
    [string]$project = "",
    [string]$type = "",
    [string]$message = ""
)

# Папки проектов
$factoryPath = "D:\content-factory"
$vpsPath     = "D:\entuziastov75-vps"

# Fallback: vps может быть в Documents
if (-not (Test-Path $vpsPath) -and (Test-Path "C:\Users\user\Documents\seo_entuziastov75")) {
    $vpsPath = "C:\Users\user\Documents\seo_entuziastov75"
}

# 1. Определяем проект: из параметра или вручную
if ($project -eq "factory") {
    $projectPath = $factoryPath
    $projectName = "content-factory"
} elseif ($project -eq "vps") {
    $projectPath = $vpsPath
    $projectName = "entuziastov75-vps"
} else {
    Write-Host "Какой проект будешь отправлять в GitHub?"
    Write-Host "1 - content-factory (агенты, SEO, контент-завод)"
    Write-Host "2 - entuziastov75-vps (тема WordPress, REST API)"
    $choice = Read-Host "Введи 1 или 2"

    if ($choice -eq "1") {
        $projectPath = $factoryPath
        $projectName = "content-factory"
    } elseif ($choice -eq "2") {
        $projectPath = $vpsPath
        $projectName = "entuziastov75-vps"
    } else {
        Write-Host "Неверный выбор. Выход."
        exit 1
    }
}

if (-not (Test-Path $projectPath)) {
    Write-Host "Ошибка: папка не найдена: $projectPath"
    exit 1
}

Set-Location $projectPath

Write-Host "`nТекущий статус $projectName`:"
git -C $projectPath status

$status = git -C $projectPath status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "`nНет изменений для коммита. Выход."
    exit 0
}

# 2. Тип и описание коммита (из параметров или интерактивно)
if (($type -ne "") -and ($message -ne "")) {
    $commitMessage = $type + ": " + $message
} else {
    Write-Host "`nВыбери тип коммита:"
    Write-Host "1 - feat"
    Write-Host "2 - fix"
    Write-Host "3 - docs"
    $typeChoice = Read-Host "Введи 1, 2 или 3"
    if ($typeChoice -eq "1") { $typePrefix = "feat" }
    elseif ($typeChoice -eq "2") { $typePrefix = "fix" }
    elseif ($typeChoice -eq "3") { $typePrefix = "docs" }
    else { Write-Host "Неверный выбор. Выход."; exit 1 }
    Write-Host "`nНапиши короткое описание:"
    $description = Read-Host "описание"
    if ($description -eq "") { Write-Host "Пустое описание. Выход."; exit 1 }
    $commitMessage = $typePrefix + ": " + $description
}

Write-Host "`nДобавляю изменения..."
git -C $projectPath add .
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Делаю коммит: '$commitMessage'"
git -C $projectPath commit -m $commitMessage
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Отправляю в GitHub (origin main)..."
git -C $projectPath push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "Ошибка push. Проверь: git pull или сеть."
    exit 1
}

Write-Host "`nDone. $projectName pushed to GitHub."
