from django.contrib import messages
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from booking.models import Booking, ServiceReview
from .models import Service, ServiceCategory


def format_price_vnd(price):
    try:
        number = int(price)
        return f'{number:,}'.replace(',', '.') + ' VND'
    except (ValueError, TypeError):
        return '0 VND'


def add_price_text(services):
    for service in services:
        service.price_text = format_price_vnd(service.price)
    return services


def home(request):
    featured_services = list(
        Service.objects
        .filter(is_active=True, is_featured=True)
        .select_related('category')
        .annotate(review_count=Count('reviews', distinct=True))
        .annotate(average_rating=Avg('reviews__rating'))
        .order_by('-id')[:3]
    )

    featured_ids = [service.id for service in featured_services]

    latest_services = list(
        Service.objects
        .filter(is_active=True)
        .exclude(id__in=featured_ids)
        .select_related('category')
        .annotate(review_count=Count('reviews', distinct=True))
        .annotate(average_rating=Avg('reviews__rating'))
        .order_by('-id')[:6]
    )

    featured_services = add_price_text(featured_services)
    latest_services = add_price_text(latest_services)

    return render(request, 'home.html', {
        'featured_services': featured_services,
        'latest_services': latest_services,
    })


def service_list(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()

    services = (
        Service.objects
        .filter(is_active=True)
        .select_related('category')
        .annotate(review_count=Count('reviews', distinct=True))
        .annotate(average_rating=Avg('reviews__rating'))
        .order_by('-id')
    )

    if query:
        services = services.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    if category_slug:
        services = services.filter(category__slug=category_slug)

    services = add_price_text(list(services))

    categories = ServiceCategory.objects.all().order_by('name')

    return render(request, 'services/service_list.html', {
        'services': services,
        'categories': categories,
        'query': query,
        'category_slug': category_slug,
    })


def service_detail(request, slug):
    service = get_object_or_404(
        Service.objects
        .select_related('category')
        .prefetch_related(
            'addons',
            'images',
            'reviews__user',
            'reviews__booking',
        ),
        slug=slug,
        is_active=True,
    )

    service.price_text = format_price_vnd(service.price)

    completed_bookings = []

    if request.user.is_authenticated:
        completed_bookings = Booking.objects.filter(
            user=request.user,
            service=service,
            status=Booking.Status.COMPLETED,
        )

        can_review = completed_bookings.exists()
    else:
        can_review = False

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Bạn cần đăng nhập để đánh giá dịch vụ.')
            return redirect('accounts:login')

        booking_id = request.POST.get('booking_id')
        rating_value = request.POST.get('rating', '0')
        comment = request.POST.get('comment', '').strip()

        try:
            rating = int(rating_value)
        except ValueError:
            rating = 0

        if rating < 1 or rating > 5:
            messages.error(request, 'Số sao đánh giá chỉ được từ 1 đến 5.')
            return redirect('services:detail', slug=service.slug)

        booking = get_object_or_404(
            Booking,
            id=booking_id,
            user=request.user,
            service=service,
            status=Booking.Status.COMPLETED,
        )

        if ServiceReview.objects.filter(booking=booking).exists():
            messages.info(request, 'Bạn đã đánh giá lịch này rồi.')
        else:
            ServiceReview.objects.create(
                booking=booking,
                service=service,
                user=request.user,
                rating=rating,
                comment=comment,
            )

            messages.success(request, 'Cảm ơn bạn đã đánh giá dịch vụ.')

        return redirect('services:detail', slug=service.slug)

    average_rating = service.reviews.aggregate(avg=Avg('rating'))['avg']

    reviews = (
        service.reviews
        .select_related('user', 'booking')
        .order_by('-created_at')
    )

    return render(request, 'services/service_detail.html', {
        'service': service,
        'average_rating': average_rating,
        'reviews': reviews,
        'completed_bookings': completed_bookings,
        'can_review': can_review,
    })


def service_suggestions(request):
    keyword = request.GET.get('q', '').strip()

    services = (
        Service.objects
        .filter(is_active=True, name__icontains=keyword)
        .values_list('name', flat=True)[:8]
    )

    return JsonResponse(list(services), safe=False)