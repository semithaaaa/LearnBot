param(
    [string]$repoName = (Split-Path -Leaf (Get-Location)),
    [ValidateSet("public","private")]
    [string]$visibility = "public",
    [string]$description = ""
)

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "Git not found. Install Git and rerun."
    exit 1
}
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error "GitHub CLI (gh) not found. Install from https://cli.github.com/ and authenticate (gh auth login)."
    exit 1
}

if (-not (Test-Path .git)) {
    git init
    git config user.email "you@example.com"
    git config user.name "Your Name"
}

git add -A
try {
    git commit -m "Initial commit" -q
} catch {
    Write-Output "Nothing to commit or commit failed; continuing."
}

$visArg = if ($visibility -eq "public") { "--public" } else { "--private" }

gh repo create $repoName $visArg --description "$description" --source . --remote origin --push

$remote = git remote get-url origin 2>$null
if ($remote) { Write-Output "Pushed to $remote" } else { Write-Output "Repository created — please verify on GitHub." }
