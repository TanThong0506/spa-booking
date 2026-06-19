from django.contrib import admin
from django.utils.html import format_html

from .models import Service, ServiceAddon, ServiceCategory, ServiceImage


def format_price_vnd(price):
    try:
        number = int(price)
        return f'{number:,}'.replace(',', '.') + ' VND'
    except (ValueError, TypeError):
        return '0 VND'


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'slug',
    ]

    search_fields = [
        'name',
        'slug',
    ]

    prepopulated_fields = {
        'slug': ('name',)
    }


class ServiceImageInline(admin.TabularInline):
    model = ServiceImage
    extra = 3

    fields = [
        'image',
        'caption',
        'image_preview',
    ]

    readonly_fields = [
        'image_preview',
    ]

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="width:120px;height:80px;object-fit:cover;border-radius:12px;border:1px solid #ddd;" />',
                obj.image.url
            )

        return 'Chưa có ảnh'

    image_preview.short_description = 'Xem ảnh'


class ServiceAddonInline(admin.StackedInline):
    model = ServiceAddon
    extra = 1

    fields = [
        'name',
        'description',
        'price',
        'is_active',
    ]

    verbose_name = 'Dịch vụ thêm'
    verbose_name_plural = 'Dịch vụ thêm'


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        'image_preview',
        'name',
        'category',
        'price_vnd_display',
        'duration_minutes',
        'is_featured',
        'is_active',
    ]

    list_filter = [
        'category',
        'is_featured',
        'is_active',
    ]

    search_fields = [
        'name',
        'description',
        'category__name',
    ]

    list_editable = [
        'is_featured',
        'is_active',
    ]

    prepopulated_fields = {
        'slug': ('name',)
    }

    fieldsets = (
        ('Thông tin dịch vụ', {
            'fields': (
                'category',
                'name',
                'slug',
                'description',
                'price',
                'duration_minutes',
            )
        }),

        ('Ảnh đại diện dịch vụ', {
            'fields': (
                'icon',
                'image',
                'main_image_preview',
            )
        }),

        ('Trạng thái hiển thị', {
            'fields': (
                'is_featured',
                'is_active',
            )
        }),
    )

    readonly_fields = [
        'main_image_preview',
    ]

    inlines = [
        ServiceImageInline,
        ServiceAddonInline,
    ]

    actions = [
        'make_featured',
        'remove_featured',
    ]

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="width:74px;height:58px;object-fit:cover;border-radius:12px;border:1px solid #ddd;" />',
                obj.image.url
            )

        return 'Chưa có ảnh'

    image_preview.short_description = 'Ảnh'

    def main_image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="max-width:300px;max-height:200px;object-fit:cover;border-radius:18px;border:1px solid #ddd;" />',
                obj.image.url
            )

        return 'Chưa có ảnh đại diện'

    main_image_preview.short_description = 'Xem ảnh đại diện'

    def price_vnd_display(self, obj):
        return format_price_vnd(obj.price)

    price_vnd_display.short_description = 'Giá tiền'

    @admin.action(description='Đánh dấu là dịch vụ nổi bật')
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)

    @admin.action(description='Bỏ dịch vụ nổi bật')
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)


@admin.register(ServiceImage)
class ServiceImageAdmin(admin.ModelAdmin):
    list_display = [
        'image_preview',
        'service',
        'caption',
    ]

    list_filter = [
        'service',
    ]

    search_fields = [
        'service__name',
        'caption',
    ]

    fields = [
        'service',
        'image',
        'caption',
        'image_preview',
    ]

    readonly_fields = [
        'image_preview',
    ]

    def image_preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="width:140px;height:92px;object-fit:cover;border-radius:14px;border:1px solid #ddd;" />',
                obj.image.url
            )

        return 'Chưa có ảnh'

    image_preview.short_description = 'Xem ảnh'


@admin.register(ServiceAddon)
class ServiceAddonAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'service',
        'price_vnd_display',
        'is_active',
    ]

    list_filter = [
        'service',
        'is_active',
    ]

    search_fields = [
        'name',
        'description',
        'service__name',
    ]

    list_editable = [
        'is_active',
    ]

    def price_vnd_display(self, obj):
        return format_price_vnd(obj.price)

    price_vnd_display.short_description = 'Giá tiền'