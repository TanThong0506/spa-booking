$ErrorActionPreference = "Stop"

Set-Location "D:\spa_booking"

Write-Host "=== Kiểm tra dự án ===" -ForegroundColor Cyan
python -m py_compile spa_booking\settings.py
python -m py_compile spa_booking\urls.py
python -m py_compile spa_booking\views.py

$env:DB_ENGINE = "sqlite"
$env:SECRET_KEY = "local-ci-check-secret"
$env:DEBUG = "False"
$env:ALLOWED_HOSTS = "localhost,127.0.0.1,testserver"
$env:SECURE_SSL_REDIRECT = "False"

python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --noinput
python manage.py test
python manage.py collectstatic --noinput

Write-Host "=== Tạo nhánh CI/CD ===" -ForegroundColor Cyan
$branch = "feature/github-cicd-render-" + (Get-Date -Format "yyyyMMdd-HHmm")
git switch -c $branch

git add -A
git status

git commit -m "ci: add GitHub Actions and Render deployment pipeline"
git push -u origin $branch

Write-Host "=== Tạo Pull Request ===" -ForegroundColor Cyan
gh pr create `
  --base main `
  --head $branch `
  --title "Triển khai CI/CD bằng GitHub Actions và Render" `
  --body "Bổ sung GitHub Actions kiểm tra Django, migration, test, static files và Docker build; cấu hình Render chỉ deploy sau khi CI thành công; bổ sung PostgreSQL, WhiteNoise, Gunicorn và health check."

gh pr view --web
