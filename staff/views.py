from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from booking.models import Booking


def staff_required(view_func):
    @wraps(view_func)
    @login_required(login_url='accounts:login')
    def wrapper(request, *args, **kwargs):
        user = request.user

        if user.is_superuser or user.groups.filter(name='Nhân viên').exists():
            return view_func(request, *args, **kwargs)

        messages.error(request, 'Bạn không có quyền truy cập trang nhân viên.')
        return redirect('home')

    return wrapper


@staff_required
def staff_dashboard(request):
    Booking.update_missed_bookings()

    bookings = (
        Booking.objects
        .filter(staff=request.user)
        .select_related('user', 'service', 'staff')
        .prefetch_related('addons')
        .order_by('-booking_date', '-booking_time')
    )

    ready_bookings = bookings.filter(
        status__in=[
            Booking.Status.CONFIRMED,
            Booking.Status.PAID,
        ],
        staff_service_status=Booking.StaffServiceStatus.READY,
    )

    serving_bookings = bookings.filter(
        staff_service_status=Booking.StaffServiceStatus.SERVING,
    )

    completed_bookings = bookings.filter(
        staff_service_status=Booking.StaffServiceStatus.DONE,
    )

    rejected_bookings = bookings.filter(
        staff_service_status=Booking.StaffServiceStatus.REJECTED,
    )

    return render(request, 'staff/dashboard.html', {
        'bookings': bookings,
        'ready_bookings': ready_bookings,
        'serving_bookings': serving_bookings,
        'completed_bookings': completed_bookings,
        'rejected_bookings': rejected_bookings,
    })


@staff_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(
        Booking.objects
        .select_related('user', 'service', 'staff')
        .prefetch_related('addons'),
        id=booking_id,
        staff=request.user,
    )

    return render(request, 'staff/booking_detail.html', {
        'booking': booking,
    })


@staff_required
def start_service(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        staff=request.user,
    )

    if booking.status not in [
        Booking.Status.CONFIRMED,
        Booking.Status.PAID,
    ]:
        messages.error(request, 'Lịch này chưa được admin xác nhận nên chưa thể bắt đầu phục vụ.')
        return redirect('staff:dashboard')

    if booking.staff_service_status == Booking.StaffServiceStatus.REJECTED:
        messages.error(request, 'Bạn đã từ chối lịch này nên không thể bắt đầu phục vụ.')
        return redirect('staff:dashboard')

    if booking.staff_service_status == Booking.StaffServiceStatus.DONE:
        messages.info(request, 'Lịch này đã phục vụ thành công.')
        return redirect('staff:dashboard')

    booking.staff_service_status = Booking.StaffServiceStatus.SERVING

    if booking.staff_started_at is None:
        booking.staff_started_at = timezone.now()

    booking.save(update_fields=[
        'staff_service_status',
        'staff_started_at',
    ])

    messages.success(request, 'Đã bắt đầu phục vụ khách hàng.')
    return redirect('staff:dashboard')


@staff_required
def complete_service(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        staff=request.user,
    )

    if booking.staff_service_status != Booking.StaffServiceStatus.SERVING:
        messages.error(request, 'Bạn cần bấm bắt đầu phục vụ trước khi hoàn tất.')
        return redirect('staff:dashboard')

    booking.staff_service_status = Booking.StaffServiceStatus.DONE
    booking.status = Booking.Status.COMPLETED

    if booking.staff_completed_at is None:
        booking.staff_completed_at = timezone.now()

    booking.save(update_fields=[
        'staff_service_status',
        'status',
        'staff_completed_at',
    ])

    messages.success(request, 'Đã cập nhật phục vụ thành công.')
    return redirect('staff:dashboard')


@staff_required
def reject_service(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        staff=request.user,
    )

    if booking.staff_service_status == Booking.StaffServiceStatus.SERVING:
        messages.error(request, 'Lịch đang phục vụ nên không thể từ chối.')
        return redirect('staff:dashboard')

    if booking.staff_service_status == Booking.StaffServiceStatus.DONE:
        messages.error(request, 'Lịch đã phục vụ xong nên không thể từ chối.')
        return redirect('staff:dashboard')

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()

        if not reason:
            messages.error(request, 'Vui lòng nhập lý do từ chối phục vụ.')
            return redirect('staff:reject_service', booking_id=booking.id)

        booking.staff_service_status = Booking.StaffServiceStatus.REJECTED
        booking.staff_reject_reason = reason

        if booking.staff_rejected_at is None:
            booking.staff_rejected_at = timezone.now()

        booking.save(update_fields=[
            'staff_service_status',
            'staff_reject_reason',
            'staff_rejected_at',
        ])

        messages.success(request, 'Đã gửi lý do từ chối phục vụ cho admin.')
        return redirect('staff:dashboard')

    return render(request, 'staff/reject_booking.html', {
        'booking': booking,
    })