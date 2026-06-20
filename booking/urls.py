from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from .views import booking_form, my_bookings, cancel_booking

from .views import (
    booking_form,
    cancel_booking,
    my_bookings,
    review_booking,
    review_detail,
)

app_name = 'booking'

urlpatterns = [
    path('', booking_form, name='form'),
    path('mine/', my_bookings, name='mine'),
    path('cancel/<int:booking_id>/', cancel_booking, name='cancel'),
    path('review/<int:booking_id>/', review_booking, name='review'),
    path(
        'review/<int:booking_id>/detail/',
        review_detail,
        name='review_detail'
    ),
]
