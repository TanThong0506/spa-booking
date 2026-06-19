from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from services.models import Service
from .models import Booking


def get_customer_name(user):
    try:
        if user.profile.name:
            return user.profile.name
    except Exception:
        pass

    if user.get_full_name():
        return user.get_full_name()

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
        booking.booking_time
    )

    if timezone.is_naive(booking_datetime):
        booking_datetime = timezone.make_aware(
            booking_datetime,
            timezone.get_current_timezone()
        )

    return booking_datetime


def is_booking_expired(booking):
    return get_booking_datetime(booking) <= timezone.now()


def can_cancel_booking(booking):
    if booking.status in [
        Booking.Status.CANCELLED,
        Booking.Status.COMPLETED
    ]:
        return False

    if is_booking_expired(booking):
        return False

    return True


@login_required
def booking_form(request):
    services = Service.objects.filter(is_active=True)

    selected_service_id = request.GET.get('service_id', '')
    customer_name = get_customer_name(request.user)
    customer_phone = get_customer_phone(request.user)
    today = timezone.localdate()

    if request.method == 'POST':
        service_id = request.POST.get('service')
        booking_date = request.POST.get('booking_date')
        booking_time = request.POST.get('booking_time')
        payment_method = request.POST.get('payment_method')
        note = request.POST.get('note', '').strip()

        selected_service_id = service_id

        if not service_id or not booking_date or not booking_time or not payment_method:
            messages.error(request, 'Vui lòng chọn đầy đủ dịch vụ, ngày, giờ và hình thức thanh toán.')
            return render(request, 'booking/booking_form.html', {
                'services': services,
                'selected_service_id': selected_service_id,
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'today': today,
            })

        service = get_object_or_404(Service, id=service_id, is_active=True)

        try:
            booking_date_obj = datetime.strptime(booking_date, '%Y-%m-%d').date()
            booking_time_obj = datetime.strptime(booking_time, '%H:%M').time()
        except ValueError:
            messages.error(request, 'Ngày hoặc giờ đặt lịch không hợp lệ.')
            return render(request, 'booking/booking_form.html', {
                'services': services,
                'selected_service_id': selected_service_id,
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'today': today,
            })

        booking_datetime = datetime.combine(booking_date_obj, booking_time_obj)
        booking_datetime = timezone.make_aware(
            booking_datetime,
            timezone.get_current_timezone()
        )

        if booking_datetime <= timezone.now():
            messages.error(request, 'Không thể đặt lịch với ngày hoặc giờ đã qua.')
            return render(request, 'booking/booking_form.html', {
                'services': services,
                'selected_service_id': selected_service_id,
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'today': today,
            })

        if payment_method not in [
            Booking.PaymentMethod.CASH,
            Booking.PaymentMethod.TRANSFER
        ]:
            messages.error(request, 'Hình thức thanh toán không hợp lệ.')
            return render(request, 'booking/booking_form.html', {
                'services': services,
                'selected_service_id': selected_service_id,
                'customer_name': customer_name,
                'customer_phone': customer_phone,
                'today': today,
            })

        Booking.objects.create(
            user=request.user,
            service=service,
            full_name=customer_name,
            phone=customer_phone,
            booking_date=booking_date_obj,
            booking_time=booking_time_obj,
            payment_method=payment_method,
            note=note,
            status=Booking.Status.PENDING
        )

        messages.success(request, 'Đặt lịch thành công. Vui lòng chờ xác nhận.')
        return redirect('booking:mine')

    return render(request, 'booking/booking_form.html', {
        'services': services,
        'selected_service_id': selected_service_id,
        'customer_name': customer_name,
        'customer_phone': customer_phone,
        'today': today,
    })


@login_required
def my_bookings(request):
    bookings = (
        Booking.objects
        .filter(user=request.user)
        .select_related('service', 'staff')
        .prefetch_related('addons')
        .order_by('-created_at')
    )

    for booking in bookings:
        booking.is_expired = is_booking_expired(booking)
        booking.can_cancel = can_cancel_booking(booking)

    return render(request, 'booking/my_bookings.html', {
        'bookings': bookings,
    })


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        user=request.user
    )

    if booking.status == Booking.Status.CANCELLED:
        messages.info(request, 'Lịch này đã được hủy trước đó.')
        return redirect('booking:mine')

    if booking.status == Booking.Status.COMPLETED:
        messages.error(request, 'Không thể hủy lịch đã hoàn tất.')
        return redirect('booking:mine')

    if is_booking_expired(booking):
        messages.error(request, 'Không thể hủy lịch vì lịch hẹn đã qua thời gian hiện tại.')
        return redirect('booking:mine')

    need_refund = (
        booking.payment_method == Booking.PaymentMethod.TRANSFER
        and booking.status == Booking.Status.CONFIRMED
    )

    if request.method == 'POST':
        cancel_reason = request.POST.get('cancel_reason', '').strip()
        cancel_reason_other = request.POST.get('cancel_reason_other', '').strip()

        refund_bank_name = request.POST.get('refund_bank_name', '').strip()
        refund_account_number = request.POST.get('refund_account_number', '').strip()
        refund_account_name = request.POST.get('refund_account_name', '').strip()

        if not cancel_reason:
            messages.error(request, 'Vui lòng chọn lý do hủy lịch.')
            return redirect('booking:cancel', booking_id=booking.id)

        if cancel_reason == Booking.CancelReason.OTHER and not cancel_reason_other:
            messages.error(request, 'Vui lòng nhập lý do hủy khác.')
            return redirect('booking:cancel', booking_id=booking.id)

        if need_refund:
            if not refund_bank_name or not refund_account_number or not refund_account_name:
                messages.error(
                    request,
                    'Lịch này đã thanh toán chuyển khoản và đã được xác nhận. Vui lòng nhập đầy đủ thông tin tài khoản để hoàn tiền.'
                )
                return redirect('booking:cancel', booking_id=booking.id)

            booking.refund_bank_name = refund_bank_name
            booking.refund_account_number = refund_account_number
            booking.refund_account_name = refund_account_name
            booking.refund_status = Booking.RefundStatus.PENDING
        else:
            booking.refund_status = Booking.RefundStatus.NONE

        booking.cancel_reason = cancel_reason
        booking.cancel_reason_other = cancel_reason_other
        booking.status = Booking.Status.CANCELLED
        booking.cancelled_at = timezone.now()
        booking.save()

        if need_refund:
            messages.success(
                request,
                'Hủy lịch thành công. Thông tin hoàn tiền đã được gửi, vui lòng chờ admin xử lý.'
            )
        else:
            messages.success(request, 'Hủy lịch thành công.')

        return redirect('booking:mine')

    return render(request, 'booking/cancel_booking.html', {
        'booking': booking,
        'need_refund': need_refund,
        'cancel_reasons': Booking.CancelReason.choices,
    })