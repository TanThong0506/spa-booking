from django.db import migrations


def seed_default_services(apps, schema_editor):
    ServiceCategory = apps.get_model('services', 'ServiceCategory')
    Service = apps.get_model('services', 'Service')
    ServiceAddon = apps.get_model('services', 'ServiceAddon')

    massage, _ = ServiceCategory.objects.get_or_create(slug='massage', defaults={'name': 'Massage'})
    skincare, _ = ServiceCategory.objects.get_or_create(slug='cham-soc-da', defaults={'name': 'Chăm sóc da'})
    haircare, _ = ServiceCategory.objects.get_or_create(slug='cham-soc-toc', defaults={'name': 'Chăm sóc tóc'})

    massage_service, _ = Service.objects.get_or_create(
        slug='massage-thu-gian',
        defaults={
            'category': massage,
            'name': 'Massage thư giãn',
            'description': 'Giúp giảm căng thẳng, thư giãn cơ thể và phục hồi năng lượng.',
            'price': 350000,
            'duration_minutes': 60,
            'icon': '💆',
            'is_featured': True,
            'is_active': True,
        },
    )
    skincare_service, _ = Service.objects.get_or_create(
        slug='cham-soc-da-mat',
        defaults={
            'category': skincare,
            'name': 'Chăm sóc da mặt',
            'description': 'Làm sạch da, dưỡng ẩm và giúp làn da khỏe đẹp hơn.',
            'price': 450000,
            'duration_minutes': 75,
            'icon': '🌿',
            'is_featured': True,
            'is_active': True,
        },
    )
    hair_service, _ = Service.objects.get_or_create(
        slug='goi-dau-duong-sinh',
        defaults={
            'category': haircare,
            'name': 'Gội đầu dưỡng sinh',
            'description': 'Massage đầu, cổ, vai, gáy giúp thư giãn và ngủ ngon hơn.',
            'price': 250000,
            'duration_minutes': 45,
            'icon': '🧖',
            'is_featured': True,
            'is_active': True,
        },
    )

    addon_data = [
        (massage_service, 'Xông tinh dầu', 'Thư giãn sâu với tinh dầu tự nhiên', 50000),
        (massage_service, 'Đá nóng', 'Tăng hiệu quả thư giãn cơ bắp', 70000),
        (skincare_service, 'Đắp mặt nạ collagen', 'Bổ sung độ ẩm cho da', 60000),
        (skincare_service, 'Peel da nhẹ', 'Hỗ trợ làm sạch da chết', 80000),
        (hair_service, 'Ủ tóc thảo mộc', 'Nuôi dưỡng tóc mềm mượt', 50000),
        (hair_service, 'Massage vai gáy', 'Giảm mỏi cổ vai gáy', 40000),
    ]

    for service, name, description, price in addon_data:
        ServiceAddon.objects.get_or_create(
            service=service,
            name=name,
            defaults={'description': description, 'price': price, 'is_active': True},
        )


def unseed_default_services(apps, schema_editor):
    ServiceAddon = apps.get_model('services', 'ServiceAddon')
    Service = apps.get_model('services', 'Service')
    ServiceCategory = apps.get_model('services', 'ServiceCategory')

    ServiceAddon.objects.all().delete()
    Service.objects.all().delete()
    ServiceCategory.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('services', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_default_services, unseed_default_services),
    ]
