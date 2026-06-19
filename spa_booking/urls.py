"""
URL configuration for spa_booking project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from services.views import home


admin.site.site_header = 'Spa Booking Admin'
admin.site.site_title = 'Spa Booking'
admin.site.index_title = 'Bảng điều khiển quản trị'


urlpatterns = [
    path('admin/', admin.site.urls),

    path('', home, name='home'),

    path('services/', include('services.urls')),
    path('booking/', include('booking.urls')),
    path('staff/', include('staff.urls')),
    path('accounts/', include('accounts.urls')),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )