from django.urls import path

from . import views

app_name = 'staff'

urlpatterns = [
    path('', views.staff_dashboard, name='dashboard'),
    path('booking/<int:booking_id>/start/', views.start_service, name='start_service'),
    path('booking/<int:booking_id>/complete/', views.complete_service, name='complete_service'),
    path('booking/<int:booking_id>/reject/', views.reject_service, name='reject_service'),
]