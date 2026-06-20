from datetime import datetime, time, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from booking.models import Booking


WORK_START = time(8, 0)
WORK_END = time(21, 0)
COMPLETE_EARLY_MINUTES = 5


def staff_required(view_func):
    @wraps(view_func)
    @login_required(login_url='accounts:login')
    def wrapper(request, *args, **kwargs):
        user = request.user

        if (
            user.is_superuser
            or user.groups.filter(name='Nhân viên').exists()
        ):
            return view_func(request, *args, **kwargs)

        messages.error(
            request,
            'Bạn không có quyền truy cập trang nhân viên.',
        )
        return redirect('home')

    return wrapper


def get_staff_name(user):
    try:
        profile_name = user.profile.name
        if profile_name:
            return profile_name
    except Exception:
        pass

    full_name = user.get_full_name()
    return full_name or user.username


def parse_selected_date(value):
    if not value:
        return timezone.localdate()

    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return timezone.localdate()


def get_booking_window(booking):
    start_datetime = booking.get_start_datetime()
    end_datetime = booking.get_end_datetime()

    if start_datetime is None:
        start_datetime = datetime.combine(
            booking.booking_date,
            booking.booking_time,
        )
        start_datetime = timezone.make_aware(
            start_datetime,
            timezone.get_current_timezone(),
        )

    if end_datetime is None:
        duration = getattr(
            booking.service,
            'duration_minutes',
            60,
        ) or 60
        end_datetime = start_datetime + timedelta(
            minutes=int(duration),
        )

    return start_datetime, end_datetime


def redirect_after_action(request, booking):
    if request.POST.get('return_to') == 'schedule':
        selected_date = request.POST.get(
            'selected_date',
            booking.booking_date.isoformat(),
        )
        return redirect(
            f'/staff/schedule/?date={selected_date}'
        )

    return redirect('staff:dashboard')


def enrich_booking(booking, now):
    start_datetime, end_datetime = get_booking_window(booking)
    complete_from = end_datetime - timedelta(
        minutes=COMPLETE_EARLY_MINUTES,
    )

    booking.start_label = timezone.localtime(
        start_datetime
    ).strftime('%H:%M')
    booking.end_label = timezone.localtime(
        end_datetime
    ).strftime('%H:%M')

    booking.room_label = (
        booking.room.name
        if booking.room
        else 'Chưa phân phòng'
    )

    booking.can_start_now = (
        booking.status in [
            Booking.Status.CONFIRMED,
            Booking.Status.PAID,
        ]
        and booking.staff_service_status
        == Booking.StaffServiceStatus.READY
        and start_datetime <= now < end_datetime
    )

    booking.can_complete_now = (
        booking.staff_service_status
        == Booking.StaffServiceStatus.SERVING
        and now >= complete_from
    )

    if (
        booking.staff_service_status
        == Booking.StaffServiceStatus.READY
        and now < start_datetime
    ):
        booking.time_message = 'Chưa tới giờ phục vụ.'
    elif (
        booking.staff_service_status
        == Booking.StaffServiceStatus.READY
        and now >= end_datetime
    ):
        booking.time_message = (
            'Ca phục vụ đã qua khung giờ làm việc.'
        )
    elif (
        booking.staff_service_status
        == Booking.StaffServiceStatus.SERVING
        and now < complete_from
    ):
        booking.time_message = (
            'Chưa tới thời gian hoàn thành. '
            'Chỉ được hoàn thành trước giờ kết thúc 5 phút.'
        )
    elif (
        booking.staff_service_status
        == Booking.StaffServiceStatus.DONE
    ):
        booking.time_message = 'Ca phục vụ đã hoàn thành.'
    elif (
        booking.staff_service_status
        == Booking.StaffServiceStatus.REJECTED
    ):
        booking.time_message = 'Ca phục vụ đã bị từ chối.'
    else:
        booking.time_message = ''

    return booking


@staff_required
def staff_dashboard(request):
    bookings = (
        Booking.objects
        .filter(staff=request.user)
        .select_related(
            'user',
            'service',
            'staff',
            'room',
        )
        .prefetch_related('addons')
        .order_by('-booking_date', '-booking_time')
    )

    ready_bookings = bookings.filter(
        status__in=[
            Booking.Status.CONFIRMED,
            Booking.Status.PAID,
        ],
        staff_service_status=(
            Booking.StaffServiceStatus.READY
        ),
    )

    serving_bookings = bookings.filter(
        staff_service_status=(
            Booking.StaffServiceStatus.SERVING
        ),
    )

    completed_bookings = bookings.filter(
        staff_service_status=(
            Booking.StaffServiceStatus.DONE
        ),
    )

    rejected_bookings = bookings.filter(
        staff_service_status=(
            Booking.StaffServiceStatus.REJECTED
        ),
    )

    return render(
        request,
        'staff/dashboard.html',
        {
            'bookings': bookings,
            'ready_bookings': ready_bookings,
            'serving_bookings': serving_bookings,
            'completed_bookings': completed_bookings,
            'rejected_bookings': rejected_bookings,
            'ready_count': ready_bookings.count(),
            'serving_count': serving_bookings.count(),
            'done_count': completed_bookings.count(),
            'rejected_count': rejected_bookings.count(),
        },
    )


@staff_required
def staff_schedule(request):
    selected_date = parse_selected_date(
        request.GET.get('date', '').strip()
    )

    week_start = selected_date - timedelta(
        days=selected_date.weekday()
    )
    week_end = week_start + timedelta(days=6)
    today = timezone.localdate()
    now = timezone.now()

    bookings = list(
        Booking.objects
        .filter(
            staff=request.user,
            booking_date__range=(week_start, week_end),
        )
        .exclude(status=Booking.Status.CANCELLED)
        .select_related(
            'user',
            'service',
            'staff',
            'room',
        )
        .prefetch_related('addons')
        .order_by('booking_date', 'booking_time')
    )

    counts = {
        Booking.StaffServiceStatus.READY: 0,
        Booking.StaffServiceStatus.SERVING: 0,
        Booking.StaffServiceStatus.DONE: 0,
        Booking.StaffServiceStatus.REJECTED: 0,
    }

    booking_map = {}

    for booking in bookings:
        enrich_booking(booking, now)

        counts[booking.staff_service_status] = (
            counts.get(booking.staff_service_status, 0) + 1
        )

        slot_minute = (
            0
            if booking.booking_time.minute < 30
            else 30
        )
        slot_key = (
            booking.booking_date,
            f'{booking.booking_time.hour:02d}:{slot_minute:02d}',
        )
        booking_map.setdefault(slot_key, []).append(booking)

    day_names = [
        'Thứ Hai',
        'Thứ Ba',
        'Thứ Tư',
        'Thứ Năm',
        'Thứ Sáu',
        'Thứ Bảy',
        'Chủ Nhật',
    ]

    week_days = []

    for index in range(7):
        current_date = week_start + timedelta(days=index)
        week_days.append({
            'name': day_names[index],
            'date': current_date,
            'date_label': current_date.strftime('%d/%m'),
            'is_today': current_date == today,
        })

    schedule_rows = []
    cursor = datetime.combine(today, WORK_START)
    last_slot = datetime.combine(today, WORK_END)

    while cursor <= last_slot:
        slot_label = cursor.strftime('%H:%M')
        cells = []

        for day in week_days:
            cells.append({
                'bookings': booking_map.get(
                    (day['date'], slot_label),
                    [],
                ),
            })

        schedule_rows.append({
            'time_label': slot_label,
            'cells': cells,
        })

        cursor += timedelta(minutes=30)

    return render(
        request,
        'staff/work_schedule.html',
        {
            'staff_name': get_staff_name(request.user),
            'selected_date_iso': selected_date.isoformat(),
            'week_start': week_start,
            'week_end': week_end,
            'previous_week': (
                week_start - timedelta(days=7)
            ).isoformat(),
            'next_week': (
                week_start + timedelta(days=7)
            ).isoformat(),
            'today_iso': today.isoformat(),
            'week_days': week_days,
            'schedule_rows': schedule_rows,
            'bookings': bookings,
            'ready_count': counts.get(
                Booking.StaffServiceStatus.READY,
                0,
            ),
            'serving_count': counts.get(
                Booking.StaffServiceStatus.SERVING,
                0,
            ),
            'done_count': counts.get(
                Booking.StaffServiceStatus.DONE,
                0,
            ),
            'rejected_count': counts.get(
                Booking.StaffServiceStatus.REJECTED,
                0,
            ),
        },
    )


@staff_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(
        Booking.objects
        .select_related(
            'user',
            'service',
            'staff',
            'room',
        )
        .prefetch_related('addons'),
        id=booking_id,
        staff=request.user,
    )

    return render(
        request,
        'staff/booking_detail.html',
        {'booking': booking},
    )


@staff_required
def start_service(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related('service'),
        id=booking_id,
        staff=request.user,
    )

    if request.method != 'POST':
        messages.error(
            request,
            'Vui lòng sử dụng nút Bắt đầu phục vụ.',
        )
        return redirect_after_action(request, booking)

    if booking.status not in [
        Booking.Status.CONFIRMED,
        Booking.Status.PAID,
    ]:
        messages.error(
            request,
            'Lịch này chưa được admin xác nhận.',
        )
        return redirect_after_action(request, booking)

    if (
        booking.staff_service_status
        == Booking.StaffServiceStatus.REJECTED
    ):
        messages.error(
            request,
            'Bạn đã từ chối lịch này.',
        )
        return redirect_after_action(request, booking)

    if (
        booking.staff_service_status
        == Booking.StaffServiceStatus.DONE
    ):
        messages.info(
            request,
            'Lịch này đã phục vụ thành công.',
        )
        return redirect_after_action(request, booking)

    if (
        booking.staff_service_status
        == Booking.StaffServiceStatus.SERVING
    ):
        messages.info(
            request,
            'Ca này đang được phục vụ.',
        )
        return redirect_after_action(request, booking)

    now = timezone.now()
    start_datetime, end_datetime = get_booking_window(
        booking
    )

    if now < start_datetime:
        messages.error(
            request,
            'Chưa tới giờ phục vụ.',
        )
        return redirect_after_action(request, booking)

    if now >= end_datetime:
        messages.error(
            request,
            'Ca phục vụ đã qua khung giờ làm việc.',
        )
        return redirect_after_action(request, booking)

    booking.staff_service_status = (
        Booking.StaffServiceStatus.SERVING
    )

    if booking.staff_started_at is None:
        booking.staff_started_at = now

    booking.save(update_fields=[
        'staff_service_status',
        'staff_started_at',
    ])

    messages.success(
        request,
        'Đã bắt đầu phục vụ khách hàng.',
    )
    return redirect_after_action(request, booking)


@staff_required
def complete_service(request, booking_id):
    booking = get_object_or_404(
        Booking.objects.select_related('service'),
        id=booking_id,
        staff=request.user,
    )

    if request.method != 'POST':
        messages.error(
            request,
            'Vui lòng sử dụng nút Hoàn thành phục vụ.',
        )
        return redirect_after_action(request, booking)

    if (
        booking.staff_service_status
        != Booking.StaffServiceStatus.SERVING
    ):
        messages.error(
            request,
            'Bạn cần bắt đầu phục vụ trước khi hoàn tất.',
        )
        return redirect_after_action(request, booking)

    now = timezone.now()
    _, end_datetime = get_booking_window(booking)
    complete_from = end_datetime - timedelta(
        minutes=COMPLETE_EARLY_MINUTES,
    )

    if now < complete_from:
        messages.error(
            request,
            (
                'Chưa tới thời gian hoàn thành. '
                'Chỉ được hoàn thành trước giờ kết thúc 5 phút.'
            ),
        )
        return redirect_after_action(request, booking)

    booking.staff_service_status = (
        Booking.StaffServiceStatus.DONE
    )
    booking.status = Booking.Status.COMPLETED

    if booking.staff_completed_at is None:
        booking.staff_completed_at = now

    booking.save(update_fields=[
        'staff_service_status',
        'status',
        'staff_completed_at',
    ])

    messages.success(
        request,
        'Đã cập nhật phục vụ thành công.',
    )
    return redirect_after_action(request, booking)


@staff_required
def reject_service(request, booking_id):
    booking = get_object_or_404(
        Booking,
        id=booking_id,
        staff=request.user,
    )

    if (
        booking.staff_service_status
        == Booking.StaffServiceStatus.SERVING
    ):
        messages.error(
            request,
            'Lịch đang phục vụ nên không thể từ chối.',
        )
        return redirect('staff:dashboard')

    if (
        booking.staff_service_status
        == Booking.StaffServiceStatus.DONE
    ):
        messages.error(
            request,
            'Lịch đã phục vụ xong nên không thể từ chối.',
        )
        return redirect('staff:dashboard')

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()

        if not reason:
            messages.error(
                request,
                'Vui lòng nhập lý do từ chối phục vụ.',
            )
            return redirect(
                'staff:reject_service',
                booking_id=booking.id,
            )

        booking.staff_service_status = (
            Booking.StaffServiceStatus.REJECTED
        )
        booking.staff_reject_reason = reason

        if booking.staff_rejected_at is None:
            booking.staff_rejected_at = timezone.now()

        booking.save(update_fields=[
            'staff_service_status',
            'staff_reject_reason',
            'staff_rejected_at',
        ])

        messages.success(
            request,
            'Đã gửi lý do từ chối phục vụ cho admin.',
        )
        return redirect('staff:dashboard')

    return render(
        request,
        'staff/reject_booking.html',
        {'booking': booking},
    )
