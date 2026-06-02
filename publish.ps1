Param(
    [string]$RemoteUrl = ""
)

function Check-Command($name) {
    return (Get-Command $name -ErrorAction SilentlyContinue) -ne $null
}

if (-not (Check-Command git)) {
    Write-Error "Git is not installed or not on PATH. Install from https://git-scm.com/downloads and re-run this script."
    exit 1
}

# Ensure git user config exists (set defaults if missing)
$userName = git config user.name
if (-not $userName) { git config user.name "Your Name" }
$userEmail = git config user.email
if (-not $userEmail) { git config user.email "you@example.com" }

if (-not (Test-Path .git)) {
    git init
}

git add -A
try {
    git commit -m "oca commit" -q
} catch {
    Write-Host "No changes to commit or commit failed; continuing."
}

if ($RemoteUrl -ne "") {
    git remote remove origin -ErrorAction SilentlyContinue
    git remote add origin $RemoteUrl
    git branch -M main
    git push -u origin main
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Push failed. Check your credentials or remote URL."
        exit 1
    }
    Write-Host "Pushed to $RemoteUrl"
} else {
    Write-Host "No remote URL provided. To push, run: .\publish.ps1 -RemoteUrl 'https://github.com/username/repo.git'"
}

Write-Host "Done. If you want, follow the README_DEPLOY.md Render steps to deploy."
