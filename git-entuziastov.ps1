# Git sync: content-factory and entuziastov75-vps to GitHub
# Run: powershell -ExecutionPolicy Bypass -File "D:\content-factory\git-entuziastov.ps1" [-project factory|vps] [-type feat|fix|docs] [-message "text"]
# Messages in ASCII to avoid encoding issues in PowerShell

param(
    [string]$project = "",
    [string]$type = "",
    [string]$message = ""
)

$factoryPath = "D:\content-factory"
$vpsPath     = "D:\entuziastov75-vps"

if (-not (Test-Path $vpsPath) -and (Test-Path "C:\Users\user\Documents\seo_entuziastov75")) {
    $vpsPath = "C:\Users\user\Documents\seo_entuziastov75"
}

if ($project -eq "factory") {
    $projectPath = $factoryPath
    $projectName = "content-factory"
} elseif ($project -eq "vps") {
    $projectPath = $vpsPath
    $projectName = "entuziastov75-vps"
} else {
    Write-Host "Project? 1 - content-factory, 2 - entuziastov75-vps"
    $choice = Read-Host "Enter 1 or 2"
    if ($choice -eq "1") {
        $projectPath = $factoryPath
        $projectName = "content-factory"
    } elseif ($choice -eq "2") {
        $projectPath = $vpsPath
        $projectName = "entuziastov75-vps"
    } else {
        Write-Host "Invalid choice. Exit."
        exit 1
    }
}

if (-not (Test-Path $projectPath)) {
    Write-Host "Error: folder not found: $projectPath"
    exit 1
}

Set-Location $projectPath

Write-Host ("`nStatus " + $projectName + ":")
git -C $projectPath status

$status = git -C $projectPath status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "`nNo changes to commit. Exit."
    exit 0
}

if (($type -ne "") -and ($message -ne "")) {
    $commitMessage = $type + ": " + $message
} else {
    Write-Host "`nCommit type: 1 - feat, 2 - fix, 3 - docs"
    $typeChoice = Read-Host "Enter 1, 2 or 3"
    if ($typeChoice -eq "1") { $typePrefix = "feat" }
    elseif ($typeChoice -eq "2") { $typePrefix = "fix" }
    elseif ($typeChoice -eq "3") { $typePrefix = "docs" }
    else { Write-Host "Invalid choice. Exit."; exit 1 }
    Write-Host "Short description:"
    $description = Read-Host "message"
    if ($description -eq "") { Write-Host "Empty description. Exit."; exit 1 }
    $commitMessage = $typePrefix + ": " + $description
}

$changedFiles = git -C $projectPath status --porcelain | ForEach-Object {
    $p = $_ -split "\s+", 3
    if ($p[2]) { $p[2] } else { $p[1] }
}
$tag = ""
$isFactory = ($project -eq "factory") -or ($projectName -eq "content-factory")
$isVps = ($project -eq "vps") -or ($projectName -eq "entuziastov75-vps")
if ($isFactory) {
    if ($changedFiles -match "^seo-agents/") { $tag = "[#agents]" }
    elseif ($changedFiles -match "^(materials/|prompts/|output/)") { $tag = "[#content]" }
} elseif ($isVps) {
    $tag = "[#site]"
}
if ($tag -ne "") {
    $commitMessage = $commitMessage -replace "^(\w+): ", "`$1: $tag "
}

Write-Host "`nAdding changes..."
git -C $projectPath add .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: git add failed. Check permissions or .gitignore."
    exit 1
}

Write-Host "Commit: '$commitMessage'"
git -C $projectPath commit -m "$commitMessage"
if ($LASTEXITCODE -ne 0) {
    $errStatus = git -C $projectPath status --porcelain
    if ([string]::IsNullOrWhiteSpace($errStatus)) {
        Write-Host "Nothing to commit (already committed?)."
    } else {
        Write-Host "Error: git commit failed. Check hooks/conflicts."
    }
    exit 1
}

Write-Host "Pushing to origin main..."
git -C $projectPath push origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: push failed. Run git pull or check network."
    exit 1
}

Write-Host ""
Write-Host ("Done. " + $projectName + " pushed to GitHub.")
