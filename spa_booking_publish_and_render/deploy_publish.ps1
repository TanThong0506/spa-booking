$ErrorActionPreference = "Stop"

Set-Location "D:\spa_booking"

git fetch origin
git switch main
git pull origin main

$branch = "feature/publish-ghcr-render-docker-" + (
    Get-Date -Format "yyyyMMdd-HHmm"
)

git switch -c $branch

New-Item `
    -ItemType Directory `
    -Force `
    -Path ".github\workflows" |
    Out-Null

Copy-Item `
    ".\spa_booking_publish_and_render\.github\workflows\publish_container.yml" `
    ".\.github\workflows\publish_container.yml" `
    -Force

Copy-Item `
    ".\spa_booking_publish_and_render\Dockerfile" `
    ".\Dockerfile" `
    -Force

Copy-Item `
    ".\spa_booking_publish_and_render\start.sh" `
    ".\start.sh" `
    -Force

Copy-Item `
    ".\spa_booking_publish_and_render\render.yaml" `
    ".\render.yaml" `
    -Force

$env:DB_ENGINE = "sqlite"
$env:SECRET_KEY = "local-ci-check-secret"
$env:DEBUG = "False"
$env:ALLOWED_HOSTS = "localhost,127.0.0.1,testserver"
$env:SECURE_SSL_REDIRECT = "False"

python manage.py check

docker build -t spa-booking:publish-test .

git add -A
git status

git commit -m "ci: publish Docker image and deploy Docker service on Render"

git push -u origin $branch

gh pr create `
    --base main `
    --head $branch `
    --title "Publish Docker image và deploy Docker lên Render" `
    --body "Bổ sung workflow publish Docker image lên GitHub Container Registry sau khi CI trên main thành công; chuyển Render sang Docker runtime; tự động migrate database và chạy Gunicorn."

gh pr view --web
