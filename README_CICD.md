# CI/CD cho dự án Spa Booking

## 1. Cấu trúc được bổ sung

```text
.github/
└── workflows/
    └── spa_booking_ci.yml

spa_booking/
├── settings.py
├── urls.py
└── views.py

Dockerfile
.dockerignore
.gitignore
.env.example
requirements.txt
build.sh
render.yaml
setup_cicd.ps1
```

## 2. Luồng CI/CD

```text
Nhánh feature
    ↓
Push và tạo Pull Request vào main
    ↓
GitHub Actions
    ├── Cài dependencies
    ├── Kiểm tra cú pháp Python
    ├── Django check
    ├── Kiểm tra migration bị thiếu
    ├── Chạy migrate với SQLite
    ├── Chạy test
    ├── Collect static
    ├── Kiểm tra /api/health/
    └── Build Docker image
    ↓
Merge vào main khi CI thành công
    ↓
Render phát hiện CI checks đã pass
    ↓
Build + migrate + collectstatic
    ↓
Chạy Gunicorn
    ↓
Health check /api/health/
```

## 3. Cài vào dự án

Giải nén toàn bộ nội dung gói này vào:

```text
D:\spa_booking
```

Cho phép chép đè:

```text
spa_booking/settings.py
spa_booking/urls.py
```

File `spa_booking/views.py` là file mới nếu dự án chưa có.

## 4. Cài thư viện local

```powershell
cd D:\spa_booking

python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Tạo file .env local

Sao chép `.env.example` thành `.env`.

Lưu ý: `settings.py` đọc trực tiếp biến môi trường của hệ điều hành.
Nó không tự nạp `.env`. Có thể tiếp tục dùng giá trị mặc định MySQL hiện tại
hoặc khai báo các biến trong Terminal/VS Code.

## 6. Kiểm tra trước khi push

PowerShell:

```powershell
cd D:\spa_booking

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
docker build -t spa-booking:local .
```

Nếu `makemigrations --check --dry-run` báo có thay đổi model:

```powershell
python manage.py makemigrations
python manage.py migrate
```

Sau đó commit cả các file migration mới.

## 7. Tạo nhánh, commit, push và Pull Request

Có thể chạy:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_cicd.ps1
```

Hoặc chạy thủ công:

```powershell
cd D:\spa_booking

git switch -c feature/github-cicd-render
git add -A
git commit -m "ci: add GitHub Actions and Render deployment pipeline"
git push -u origin feature/github-cicd-render

gh pr create `
  --base main `
  --head feature/github-cicd-render `
  --title "Triển khai CI/CD bằng GitHub Actions và Render" `
  --body "Bổ sung CI kiểm tra Django, migration, test, static files, Docker build và CD lên Render sau khi CI thành công."
```

## 8. Tạo dịch vụ trên Render

1. Mở Render Dashboard.
2. Chọn **Blueprints**.
3. Chọn **New Blueprint Instance**.
4. Kết nối repository `TanThong0506/spa-booking`.
5. Render đọc `render.yaml`.
6. Chọn **Apply**.

Blueprint tạo:

- Web service `spa-booking`
- PostgreSQL database `spa-booking-db`
- Biến `DATABASE_URL`
- `SECRET_KEY` tự sinh
- Health check `/api/health/`
- Auto deploy: **After CI Checks Pass**

Không cần tạo `RENDER_DEPLOY_HOOK_URL` vì `render.yaml` dùng
`autoDeployTrigger: checksPass`.

## 9. Tạo tài khoản admin trên Render

Sau khi deploy thành công, mở Render Shell và chạy:

```bash
python manage.py createsuperuser
```

## 10. Lưu ý về ảnh upload

Render web service dùng filesystem tạm thời. Ảnh người dùng tải lên thư mục
`media/` có thể mất sau lần deploy tiếp theo.

Để lưu ảnh lâu dài, sử dụng một trong các cách:

- Render Persistent Disk
- Cloudinary
- Amazon S3 hoặc dịch vụ object storage khác

Các ảnh có sẵn được commit trong repository vẫn được đưa vào bản deploy,
nhưng ảnh tải lên trong lúc ứng dụng đang chạy không nên lưu trên filesystem tạm.
