from django.db import models


class ServiceCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Danh mục dịch vụ'
        verbose_name_plural = 'Danh mục dịch vụ'

    def __str__(self):
        return self.name


class Service(models.Model):
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        related_name='services',
        verbose_name='Danh mục'
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name='Dịch vụ nổi bật'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Đang hoạt động'
    )

    name = models.CharField(max_length=160, verbose_name='Tên dịch vụ')
    slug = models.SlugField(max_length=180, unique=True)

    description = models.TextField(verbose_name='Mô tả')
    price = models.PositiveIntegerField(verbose_name='Giá dịch vụ')
    duration_minutes = models.PositiveIntegerField(default=60, verbose_name='Thời gian thực hiện')

    icon = models.CharField(max_length=8, default='💆', verbose_name='Biểu tượng')

    # Ảnh chính của dịch vụ
    image = models.ImageField(
        upload_to='services/main/',
        blank=True,
        null=True,
        verbose_name='Ảnh chính'
    )

    is_featured = models.BooleanField(default=False, verbose_name='Dịch vụ nổi bật')
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')

    class Meta:
        ordering = ['name']
        verbose_name = 'Dịch vụ'
        verbose_name_plural = 'Dịch vụ'

    def __str__(self):
        return self.name


class ServiceImage(models.Model):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Dịch vụ'
    )

    image = models.ImageField(
        upload_to='services/gallery/',
        verbose_name='Hình ảnh chi tiết'
    )

    caption = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Chú thích'
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'Hình ảnh dịch vụ'
        verbose_name_plural = 'Hình ảnh dịch vụ'

    def __str__(self):
        return f'Ảnh của {self.service.name}'


class ServiceAddon(models.Model):
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='addons',
        verbose_name='Dịch vụ'
    )

    name = models.CharField(max_length=160, verbose_name='Tên menu thêm')
    description = models.CharField(max_length=255, blank=True, verbose_name='Mô tả')
    price = models.PositiveIntegerField(default=0, verbose_name='Giá thêm')
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')

    class Meta:
        ordering = ['name']
        verbose_name = 'Dịch vụ thêm'
        verbose_name_plural = 'Dịch vụ thêm'

    def __str__(self):
        return f'{self.service.name} - {self.name}'
    @property
    def price_vnd(self):
        try:
            number = int(self.price)
            formatted = f'{number:,}'.replace(',', '.')
            return f'{formatted} VND'
        except (ValueError, TypeError):
            return '0 VND'