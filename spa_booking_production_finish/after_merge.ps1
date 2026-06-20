$ErrorActionPreference = "Stop"

Set-Location "D:\spa_booking"

git switch main
git pull origin main

Write-Host "Triggering Docker package publication..."
gh workflow run publish_container.yml `
    --ref main `
    --repo TanThong0506/spa-booking

Start-Sleep -Seconds 8

$runId = gh run list `
    --repo TanThong0506/spa-booking `
    --workflow publish_container.yml `
    --branch main `
    --limit 1 `
    --json databaseId `
    --jq ".[0].databaseId"

if (-not $runId) {
    throw "Could not find the Publish Docker Package run."
}

Write-Host "Watching workflow run $runId..."
gh run watch $runId `
    --repo TanThong0506/spa-booking `
    --exit-status

Write-Host "Opening GitHub package page..."
Start-Process `
    "https://github.com/TanThong0506/spa-booking/pkgs/container/spa-booking"

Write-Host ""
Write-Host "GitHub Package completed."
Write-Host "Next: Render Dashboard -> New -> Blueprint -> select spa-booking -> Apply."
