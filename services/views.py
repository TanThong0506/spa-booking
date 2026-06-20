from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render

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
        .annotate(
            review_count=Count('reviews', distinct=True),
            average_rating=Avg('reviews__rating'),
        )
        .order_by('-id')[:3]
    )

    featured_ids = [
        service.id
        for service in featured_services
    ]

    latest_services = list(
        Service.objects
        .filter(is_active=True)
        .exclude(id__in=featured_ids)
        .select_related('category')
        .annotate(
            review_count=Count('reviews', distinct=True),
            average_rating=Avg('reviews__rating'),
        )
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
        .annotate(
            review_count=Count('reviews', distinct=True),
            average_rating=Avg('reviews__rating'),
        )
        .order_by('-id')
    )

    if query:
        services = services.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    if category_slug:
        services = services.filter(
            category__slug=category_slug
        )

    services = add_price_text(list(services))

    categories = (
        ServiceCategory.objects
        .all()
        .order_by('name')
    )

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
        ),
        slug=slug,
        is_active=True,
    )

    service.price_text = format_price_vnd(service.price)

    review_queryset = (
        ServiceReview.objects
        .filter(service=service)
        .select_related(
            'user',
            'booking',
        )
        .order_by('-created_at')
    )

    selected_rating = request.GET.get(
        'rating',
        'all'
    ).strip()

    valid_ratings = [
        'all',
        '1',
        '2',
        '3',
        '4',
        '5',
    ]

    if selected_rating not in valid_ratings:
        selected_rating = 'all'

    if selected_rating == 'all':
        reviews = review_queryset
    else:
        reviews = review_queryset.filter(
            rating=int(selected_rating)
        )

    reviews = list(reviews)

    for review in reviews:
        full_name = review.user.get_full_name().strip()

        if full_name:
            review.display_name = full_name
        else:
            review.display_name = review.user.username

    rating_counts = review_queryset.aggregate(
        total=Count('id'),
        rating_5=Count(
            'id',
            filter=Q(rating=5),
        ),
        rating_4=Count(
            'id',
            filter=Q(rating=4),
        ),
        rating_3=Count(
            'id',
            filter=Q(rating=3),
        ),
        rating_2=Count(
            'id',
            filter=Q(rating=2),
        ),
        rating_1=Count(
            'id',
            filter=Q(rating=1),
        ),
    )

    rating_filters = [
        {
            'value': 'all',
            'label': 'Tất cả',
            'count': rating_counts['total'],
        },
        {
            'value': '5',
            'label': '5 sao',
            'count': rating_counts['rating_5'],
        },
        {
            'value': '4',
            'label': '4 sao',
            'count': rating_counts['rating_4'],
        },
        {
            'value': '3',
            'label': '3 sao',
            'count': rating_counts['rating_3'],
        },
        {
            'value': '2',
            'label': '2 sao',
            'count': rating_counts['rating_2'],
        },
        {
            'value': '1',
            'label': '1 sao',
            'count': rating_counts['rating_1'],
        },
    ]

    rating_summary = review_queryset.aggregate(
        average_rating=Avg('rating'),
        review_count=Count('id'),
    )

    average_rating = (
        rating_summary['average_rating']
        or 0
    )

    review_count = (
        rating_summary['review_count']
        or 0
    )

    completed_bookings = Booking.objects.none()
    can_review = False

    if request.user.is_authenticated:
        reviewed_booking_ids = (
            ServiceReview.objects
            .filter(
                user=request.user,
                service=service,
            )
            .values_list(
                'booking_id',
                flat=True,
            )
        )

        completed_bookings = (
            Booking.objects
            .filter(
                user=request.user,
                service=service,
                status=Booking.Status.COMPLETED,
            )
            .exclude(
                id__in=reviewed_booking_ids
            )
            .order_by(
                '-booking_date',
                '-booking_time',
            )
        )

        can_review = completed_bookings.exists()

    return render(request, 'services/service_detail.html', {
        'service': service,
        'average_rating': average_rating,
        'review_count': review_count,
        'reviews': reviews,
        'selected_rating': selected_rating,
        'rating_filters': rating_filters,
        'completed_bookings': completed_bookings,
        'can_review': can_review,
    })


def service_suggestions(request):
    keyword = request.GET.get('q', '').strip()

    services = (
        Service.objects
        .filter(
            is_active=True,
            name__icontains=keyword,
        )
        .values_list(
            'name',
            flat=True,
        )[:8]
    )

    return JsonResponse(
        list(services),
        safe=False,
    )
