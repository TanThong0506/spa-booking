"""URL configuration for spa_booking project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from services.views import home
from spa_booking.views import health_check

admin.site.site_header = "Spa Booking Admin"
admin.site.site_title = "Spa Booking"
admin.site.index_title = "Bảng điều khiển quản trị"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("api/health/", health_check, name="health_check"),
    path("services/", include("services.urls")),
    path("booking/", include("booking.urls")),
    path("staff/", include("staff.urls")),
    path("accounts/", include("accounts.urls")),
]

handler400 = "spa_booking.error_handlers.bad_request"
handler403 = "spa_booking.error_handlers.permission_denied"
handler404 = "spa_booking.error_handlers.page_not_found"
handler500 = "spa_booking.error_handlers.server_error"

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
