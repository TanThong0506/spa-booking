from django.urls import path

from .views import service_detail, service_list

app_name = 'services'

urlpatterns = [
    path('', service_list, name='list'),
    path('<slug:slug>/', service_detail, name='detail'),
]