from datetime import datetime, time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from services.models import Service
from .models import Booking, ServiceReview


def get_customer_name(user):
    try:
        if user.profile.name:
            return user.profile.name
    except Exception:
        pass

    full_name = user.get_full_name()

    if full_name:
        return full_name

    return 'Khách hàng'


def get_customer_phone(user):
    try:
        if user.profile.phone:
            return user.profile.phone
    except Exception:
        pass

    return user.username


def get_booking_datetime(booking):
    booking_datetime = datetime.combine(
        booking.booking_date,
        booking.booking_time,
    )

    if timezone.is_naive(booking_datetime):
        booking_datetime = timezone.make_aware(
            booking_datetime,
            timezone.get_current_timezone(),
        )

    return booking_datetime


def is_booking_expired(booking):
    return get_booking_datetime(booking) <= timezone.now()


def can_cancel_booking(booking):
    cancellable_statuses = [
        Booking.Status.PENDING,
        Booking.Status.PAID,
        Booking.Status.CONFIRMED,
    ]

    if booking.status not in cancellable_statuses:
        return False

    return not is_booking_expired(booking)


def can_update_booking(booking):
    # Có nút cập nhật ở cùng những lịch còn được phép hủy.
    return can_cancel_booking(booking)


def booking_form_context(
    request,
    services,
    selected_service_id,
    customer_name,
    customer_phone,
    today,
):
    return {
        'services': services,
        'selected_service_id': selected_service_id,
        'customer_name': customer_name,
        'customer_phone': customer_phone,
        'today': today,
    }


@login_required
def booking_form(request):
    services = (
        Service.objects
        .filter(is_active=True)
        .order_by('name')
    )

    selected_service_id = request.GET.get(
        'service_id',
        '',
    )

    customer_name = get_customer_name(request.user)
    customer_phone = get_customer_phone(request.user)
    today = timezone.localdate()

    if request.method == 'POST':
        service_id = request.POST.get(
            'service',
            '',
        ).strip()

        booking_date_value = request.POST.get(
            'booking_date',
            '',
        ).strip()

        booking_time_value = request.POST.get(
            'booking_time',
            '',
        ).strip()

        guest_count_value = request.POST.get(
            'guest_count',
            '1',
        ).strip()

        payment_method = request.POST.get(
            'payment_method',
            '',
        ).strip()

        note = request.POST.get(
            'note',
            '',
        ).strip()

        selected_service_id = service_id

        context = booking_form_context(
            request=request,
            services=services,
            selected_service_id=selected_service_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            today=today,
        )

        if not all([
            service_id,
            booking_date_value,
            booking_time_value,
            payment_method,
        ]):
            messages.error(
                request,
                (
                    'Vui lòng chọn đầy đủ dịch vụ, ngày, giờ, '
                    'số lượng khách và hình thức thanh toán.'
                ),
            )
            return render(
                request,
                'booking/booking_form.html',
                context,
            )

        service = get_object_or_404(
            Service,
            id=service_id,
            is_active=True,
        )

        try:
            booking_date_obj = datetime.strptime(
                booking_date_value,
                '%Y-%m-%d',
            ).date()

            booking_time_obj = datetime.strptime(
                booking_time_value,
                '%H:%M',
            ).time()

            guest_count = int(guest_count_value)
        except (TypeError, ValueError):
            messages.error(
                request,
                'Ngày, giờ hoặc số lượng khách không hợp lệ.',
            )
            return render(
                request,
                'booking/booking_form.html',
                context,
            )

        booking_datetime = datetime.combine(
            booking_date_obj,
            booking_time_obj,
        )

        if timezone.is_naive(booking_datetime):
            booking_datetime = timezone.make_aware(
                booking_datetime,
                timezone.get_current_timezone(),
            )

        if booking_datetime <= timezone.now():
            messages.error(
                request,
                'Không thể đặt lịch với ngày hoặc giờ đã qua.',
            )
            return render(
                request,
                'booking/booking_form.html',
                context,
            )

        if not (
            time(8, 0)
            <= booking_time_obj
            <= time(21, 0)
        ):
            messages.error(
                request,
                'Giờ đặt phải nằm trong khoảng 08:00 đến 21:00.',
            )
            return render(
                request,
                'booking/booking_form.html',
                context,
            )

        if guest_count < 1 or guest_count > 50:
            messages.error(
                request,
                'Số lượng khách phải từ 1 đến 50.',
            )
            return render(
                request,
                'booking/booking_form.html',
                context,
            )

        if payment_method not in [
            Booking.PaymentMethod.CASH,
            Booking.PaymentMethod.TRANSFER,
        ]:
            messages.error(
                request,
                'Hình thức thanh toán không hợp lệ.',
            )
            return render(
                request,
                'booking/booking_form.html',
                context,
            )

        Booking.objects.create(
            user=request.user,
            service=service,
            full_name=customer_name,
            phone=customer_phone,
            booking_date=booking_date_obj,
            booking_time=booking_time_obj,
            guest_count=guest_count,
            payment_method=payment_method,
            note=note,
            status=Booking.Status.PENDING,
        )

        messages.success(
            request,
            'Đặt lịch thành công. Vui lòng chờ xác nhận.',
        )

        return redirect('booking:mine')

    return render(
        request,
        'booking/booking_form.html',
        booking_form_context(
            request=request,
            services=services,
            selected_service_id=selected_service_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            today=today,
        ),
    )


@login_required
def my_bookings(request):
    bookings = (
        Booking.objects
        .filter(user=request.user)
        .select_related(
            'service',
            'staff',
            'room',
        )
        .prefetch_related('addons')
        .order_by('-created_at')
    )

    for booking in bookings:
        booking.is_expired = is_booking_expired(booking)
        booking.can_cancel = can_cancel_booking(booking)
        booking.can_update = can_update_booking(booking)

        booking.has_review = ServiceReview.objects.filter(
            booking=booking,
        ).exists()

        booking.can_review = (
            booking.status == Booking.Status.COMPLETED
            and not booking.has_review
        )

    return render(
        request,
        'booking/my_bookings.html',
        {
            'bookings': bookings,
        },
    )


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related(
            'service',
            'room',
            'staff',
        ),
        id=booking_id,
        user=request.user,
    )

    if not can_cancel_booking(booking):
        messages.error(
            request,
            'Lịch này không thể hủy.',
        )
        return redirect('booking:mine')

    need_refund = (
        booking.payment_method
        == Booking.PaymentMethod.TRANSFER
    )

    context = {
        'booking': booking,
        'need_refund': need_refund,
        'cancel_reason_choices': Booking.CancelReason.choices,
        'cancel_reasons': Booking.CancelReason.choices,
    }

    if request.method == 'POST':
        cancel_reason = request.POST.get(
            'cancel_reason',
            '',
        ).strip()

        cancel_reason_other = request.POST.get(
            'cancel_reason_other',
            '',
        ).strip()

        valid_reasons = {
            value
            for value, label in Booking.CancelReason.choices
        }

        if cancel_reason not in valid_reasons:
            messages.error(
                request,
                'Vui lòng chọn lý do hủy lịch.',
            )
            return render(
                request,
                'booking/cancel_booking.html',
                context,
            )

        if (
            cancel_reason == Booking.CancelReason.OTHER
            and not cancel_reason_other
        ):
            messages.error(
                request,
                'Vui lòng nhập chi tiết lý do hủy khác.',
            )
            return render(
                request,
                'booking/cancel_booking.html',
                context,
            )

        booking.cancel_reason = cancel_reason
        booking.cancel_reason_other = cancel_reason_other
        booking.cancelled_at = timezone.now()
        booking.status = Booking.Status.CANCELLED

        if need_refund:
            refund_bank_name = request.POST.get(
                'refund_bank_name',
                '',
            ).strip()

            refund_account_number = request.POST.get(
                'refund_account_number',
                '',
            ).strip()

            refund_account_name = request.POST.get(
                'refund_account_name',
                '',
            ).strip()

            if not all([
                refund_bank_name,
                refund_account_number,
                refund_account_name,
            ]):
                messages.error(
                    request,
                    (
                        'Vui lòng nhập đầy đủ ngân hàng, '
                        'số tài khoản và tên chủ tài khoản '
                        'để admin xử lý hoàn tiền.'
                    ),
                )
                return render(
                    request,
                    'booking/cancel_booking.html',
                    context,
                )

            booking.refund_bank_name = refund_bank_name
            booking.refund_account_number = (
                refund_account_number
            )
            booking.refund_account_name = (
                refund_account_name
            )
            booking.refund_status = (
                Booking.RefundStatus.PENDING
            )
            booking.refunded_at = None

            success_message = (
                'Hủy lịch thành công. Thông tin tài khoản '
                'đã được gửi đến admin. Vui lòng chờ xử lý '
                'hoàn tiền.'
            )
        else:
            booking.refund_status = Booking.RefundStatus.NONE
            booking.refund_bank_name = ''
            booking.refund_account_number = ''
            booking.refund_account_name = ''
            booking.refunded_at = None

            success_message = 'Hủy lịch thành công.'

        booking.save(
            update_fields=[
                'status',
                'cancel_reason',
                'cancel_reason_other',
                'cancelled_at',
                'refund_status',
                'refund_bank_name',
                'refund_account_number',
                'refund_account_name',
                'refunded_at',
            ],
        )

        messages.success(
            request,
            success_message,
        )

        return redirect('booking:mine')

    return render(
        request,
        'booking/cancel_booking.html',
        context,
    )


@login_required
def update_booking(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related('service'),
        id=booking_id,
        user=request.user,
    )

    if not can_update_booking(booking):
        messages.error(
            request,
            (
                'Chỉ có thể cập nhật lịch đang chờ xác nhận '
                'và chưa đến thời gian phục vụ.'
            ),
        )
        return redirect('booking:mine')

    services = (
        Service.objects
        .filter(is_active=True)
        .order_by('name')
    )

    if request.method == 'POST':
        service_id = request.POST.get(
            'service',
            '',
        ).strip()

        booking_date_value = request.POST.get(
            'booking_date',
            '',
        ).strip()

        booking_time_value = request.POST.get(
            'booking_time',
            '',
        ).strip()

        guest_count_value = request.POST.get(
            'guest_count',
            '1',
        ).strip()

        note_value = request.POST.get(
            'note',
            '',
        ).strip()

        selected_service_id = service_id

        try:
            service = Service.objects.get(
                id=service_id,
                is_active=True,
            )

            booking_date_obj = datetime.strptime(
                booking_date_value,
                '%Y-%m-%d',
            ).date()

            booking_time_obj = datetime.strptime(
                booking_time_value,
                '%H:%M',
            ).time()

            guest_count = int(guest_count_value)
        except (
            Service.DoesNotExist,
            TypeError,
            ValueError,
        ):
            messages.error(
                request,
                'Thông tin cập nhật không hợp lệ.',
            )
        else:
            booking_datetime = datetime.combine(
                booking_date_obj,
                booking_time_obj,
            )

            if timezone.is_naive(booking_datetime):
                booking_datetime = timezone.make_aware(
                    booking_datetime,
                    timezone.get_current_timezone(),
                )

            if booking_datetime <= timezone.now():
                messages.error(
                    request,
                    'Ngày và giờ đặt phải ở tương lai.',
                )
            elif not (
                time(8, 0)
                <= booking_time_obj
                <= time(21, 0)
            ):
                messages.error(
                    request,
                    (
                        'Giờ đặt phải nằm trong khoảng '
                        '08:00 đến 21:00.'
                    ),
                )
            elif guest_count < 1 or guest_count > 50:
                messages.error(
                    request,
                    'Số lượng khách phải từ 1 đến 50.',
                )
            else:
                service_changed = (
                    booking.service_id != service.id
                )

                previous_status = booking.status

                booking.service = service
                booking.booking_date = booking_date_obj
                booking.booking_time = booking_time_obj
                booking.guest_count = guest_count
                booking.note = note_value

                update_fields = [
                    'service',
                    'booking_date',
                    'booking_time',
                    'guest_count',
                    'note',
                ]

                # Lịch đã được duyệt mà khách thay đổi thông tin
                # phải được admin duyệt và phân phòng lại.
                if previous_status == Booking.Status.CONFIRMED:
                    if (
                        booking.payment_method
                        == Booking.PaymentMethod.TRANSFER
                    ):
                        booking.status = Booking.Status.PAID
                    else:
                        booking.status = Booking.Status.PENDING

                    booking.room = None
                    booking.staff = None
                    booking.staff_service_status = (
                        Booking.StaffServiceStatus.READY
                    )
                    booking.staff_reject_reason = ''
                    booking.staff_started_at = None
                    booking.staff_completed_at = None
                    booking.staff_rejected_at = None

                    update_fields.extend([
                        'status',
                        'room',
                        'staff',
                        'staff_service_status',
                        'staff_reject_reason',
                        'staff_started_at',
                        'staff_completed_at',
                        'staff_rejected_at',
                    ])

                booking.save(update_fields=update_fields)

                if service_changed:
                    booking.addons.clear()

                messages.success(
                    request,
                    'Cập nhật lịch đặt thành công.',
                )

                return redirect('booking:mine')
    else:
        selected_service_id = str(
            booking.service_id
        )

        booking_date_value = (
            booking.booking_date.strftime('%Y-%m-%d')
        )

        booking_time_value = (
            booking.booking_time.strftime('%H:%M')
        )

        guest_count_value = str(
            booking.guest_count or 1
        )

        note_value = booking.note or ''

    return render(
        request,
        'booking/update_booking.html',
        {
            'booking': booking,
            'services': services,
            'today': timezone.localdate(),
            'selected_service_id': selected_service_id,
            'booking_date_value': booking_date_value,
            'booking_time_value': booking_time_value,
            'guest_count_value': guest_count_value,
            'note_value': note_value,
        },
    )


@login_required
def review_booking(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related('service'),
        id=booking_id,
        user=request.user,
        status=Booking.Status.COMPLETED,
    )

    existing_review = ServiceReview.objects.filter(
        booking=booking,
    ).first()

    if existing_review:
        messages.info(
            request,
            'Lịch sử dụng này đã được đánh giá trước đó.',
        )

        return redirect(
            'booking:review_detail',
            booking_id=booking.id,
        )

    if request.method == 'POST':
        rating_value = request.POST.get(
            'rating',
            '',
        ).strip()

        comment = request.POST.get(
            'comment',
            '',
        ).strip()

        try:
            rating = int(rating_value)
        except (TypeError, ValueError):
            rating = 0

        if rating < 1 or rating > 5:
            messages.error(
                request,
                'Vui lòng chọn số sao từ 1 đến 5.',
            )

            return render(
                request,
                'booking/review_form.html',
                {
                    'booking': booking,
                    'selected_rating': rating_value,
                    'comment': comment,
                },
            )

        ServiceReview.objects.create(
            booking=booking,
            service=booking.service,
            user=request.user,
            rating=rating,
            comment=comment,
        )

        messages.success(
            request,
            'Đánh giá của bạn đã được lưu thành công.',
        )

        return redirect(
            'booking:review_detail',
            booking_id=booking.id,
        )

    return render(
        request,
        'booking/review_form.html',
        {
            'booking': booking,
        },
    )


@login_required
def review_detail(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related('service'),
        id=booking_id,
        user=request.user,
        status=Booking.Status.COMPLETED,
    )

    review = get_object_or_404(
        ServiceReview,
        booking=booking,
        user=request.user,
    )

    return render(
        request,
        'booking/review_detail.html',
        {
            'booking': booking,
            'review': review,
        },
    )
