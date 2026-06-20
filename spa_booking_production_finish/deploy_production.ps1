$ErrorActionPreference = "Stop"

Set-Location "D:\spa_booking"

Write-Host "Checking GitHub CLI authentication..."
gh auth status

Write-Host "Checking Docker Desktop..."
docker info | Out-Null

git fetch origin
git switch main
git pull origin main

$branch = "fix/production-render-ghcr-" + (
    Get-Date -Format "yyyyMMdd-HHmm"
)

git switch -c $branch

New-Item `
    -ItemType Directory `
    -Force `
    -Path ".github\workflows" |
    Out-Null

Copy-Item `
    ".\spa_booking_production_finish\spa_booking\settings.py" `
    ".\spa_booking\settings.py" `
    -Force

Copy-Item `
    ".\spa_booking_production_finish\spa_booking\urls.py" `
    ".\spa_booking\urls.py" `
    -Force

Copy-Item `
    ".\spa_booking_production_finish\spa_booking\views.py" `
    ".\spa_booking\views.py" `
    -Force

Copy-Item `
    ".\spa_booking_production_finish\Dockerfile" `
    ".\Dockerfile" `
    -Force

Copy-Item `
    ".\spa_booking_production_finish\start.sh" `
    ".\start.sh" `
    -Force

Copy-Item `
    ".\spa_booking_production_finish\render.yaml" `
    ".\render.yaml" `
    -Force

Copy-Item `
    ".\spa_booking_production_finish\.github\workflows\publish_container.yml" `
    ".\.github\workflows\publish_container.yml" `
    -Force

$env:DB_ENGINE = "sqlite"
$env:SECRET_KEY = "local-production-check-secret"
$env:DEBUG = "False"
$env:ALLOWED_HOSTS = "localhost,127.0.0.1,testserver"
$env:CSRF_TRUSTED_ORIGINS = "http://localhost,http://127.0.0.1"
$env:SECURE_SSL_REDIRECT = "False"
$env:SESSION_COOKIE_SECURE = "False"
$env:CSRF_COOKIE_SECURE = "False"

python manage.py check
python manage.py migrate --noinput
python manage.py collectstatic --noinput

$response = python manage.py shell -c @"
from django.test import Client
response = Client().get('/api/health/')
print(response.status_code)
print(response.content.decode())
assert response.status_code == 200
"@

Write-Host $response

docker build `
    --progress=plain `
    --tag "spa-booking:production-test" `
    .

git add -A
git status

git commit `
    -m "fix: complete production Docker GHCR and Render deployment"

git push -u origin $branch

gh pr create `
    --base main `
    --head $branch `
    --title "Hoàn thiện Docker Package và Render production" `
    --body "Cấu hình settings production bằng biến môi trường và DATABASE_URL; thêm health endpoint; chạy migrate trước Gunicorn; bổ sung workflow publish GHCR có thể chạy thủ công; hoàn thiện Render Docker Blueprint."

gh pr view --web
