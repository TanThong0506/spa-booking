
"""URL configuration for spa_booking project."""

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from services.views import home
from spa_booking.views import health_check


# Tùy chỉnh giao diện Django Admin
admin.site.site_header = "Spa Booking Admin"
admin.site.site_title = "Spa Booking"
admin.site.index_title = "Bảng điều khiển quản trị"


urlpatterns = [
    # Django Admin
    path("admin/", admin.site.urls),

    # Trang chủ
    path("", home, name="home"),

    # API kiểm tra trạng thái hệ thống
    path(
        "api/health/",
        health_check,
        name="health_check",
    ),

    # Các ứng dụng
    path(
        "services/",
        include("services.urls"),
    ),
    path(
        "booking/",
        include("booking.urls"),
    ),
    path(
        "staff/",
        include("staff.urls"),
    ),
    path(
        "accounts/",
        include("accounts.urls"),
    ),

    # Phục vụ ảnh trong thư mục media
    # Hoạt động trên cả localhost và Render
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {
            "document_root": settings.MEDIA_ROOT,
        },
    ),
]


# Các trang xử lý lỗi
handler400 = "spa_booking.error_handlers.bad_request"
handler403 = "spa_booking.error_handlers.permission_denied"
handler404 = "spa_booking.error_handlers.page_not_found"
handler500 = "spa_booking.error_handlers.server_error"

