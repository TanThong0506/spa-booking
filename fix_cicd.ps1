$ErrorActionPreference = "Stop"

Set-Location "D:\spa_booking"

git fetch origin
git switch main
git pull origin main

$branch = "fix/cicd-docker-build-" + (Get-Date -Format "yyyyMMdd-HHmm")
git switch -c $branch

Copy-Item `
  ".\spa_booking_cicd_fix\.github\workflows\spa_booking_ci.yml" `
  ".\.github\workflows\spa_booking_ci.yml" `
  -Force

Copy-Item `
  ".\spa_booking_cicd_fix\Dockerfile" `
  ".\Dockerfile" `
  -Force

# Loại bỏ toàn bộ Python cache đang bị Git theo dõi.
$trackedCache = git ls-files | Where-Object {
    $_ -like "*__pycache__*" -or $_ -like "*.pyc"
}

foreach ($file in $trackedCache) {
    git rm --cached --ignore-unmatch -- "$file"
}

Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" |
    Remove-Item -Recurse -Force

python manage.py check

git add -A
git status

git commit -m "fix: repair Docker build and update GitHub Actions"

git push -u origin $branch

gh pr create `
  --base main `
  --head $branch `
  --title "Sửa lỗi Docker Build trong CI/CD" `
  --body "Sửa cú pháp CMD trong Dockerfile, thay Buildx action bằng docker build trực tiếp, cập nhật GitHub Actions lên phiên bản mới và loại bỏ các file __pycache__ khỏi repository."

gh pr view --web
