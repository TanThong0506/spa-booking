from django.urls import path

from .views import (
    booking_form,
    cancel_booking,
    my_bookings,
    review_booking,
    review_detail,
    update_booking,
)

app_name = 'booking'

urlpatterns = [
    path('', booking_form, name='form'),
    path('mine/', my_bookings, name='mine'),

    path(
        'cancel/<int:booking_id>/',
        cancel_booking,
        name='cancel',
    ),

    path(
        'update/<int:booking_id>/',
        update_booking,
        name='update',
    ),

    path(
        'review/<int:booking_id>/',
        review_booking,
        name='review',
    ),

    path(
        'review/<int:booking_id>/detail/',
        review_detail,
        name='review_detail',
    ),
]
