from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'created_at']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['created_at']
