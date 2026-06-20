from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Room(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Sẵn sàng'
        MAINTENANCE = 'maintenance', 'Đang bảo trì'
        INACTIVE = 'inactive', 'Ngừng hoạt động'

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Tên phòng',
    )

    capacity = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Sức chứa',
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        verbose_name='Trạng thái',
    )

    description = models.TextField(
        blank=True,
        verbose_name='Mô tả',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Ngày cập nhật',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Phòng'
        verbose_name_plural = 'Quản lý phòng'

    def __str__(self):
        return f'{self.name} - sức chứa {self.capacity}'


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Chờ xác nhận'
        PAID = 'paid', 'Đã thanh toán'
        CONFIRMED = 'confirmed', 'Đã được duyệt'
        COMPLETED = 'completed', 'Đã phục vụ'
        MISSED = 'missed', 'Bỏ sót'
        CANCELLED = 'cancelled', 'Đã hủy'

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Tiền mặt'
        TRANSFER = 'transfer', 'Chuyển khoản'

    class CancelReason(models.TextChoices):
        CHANGE_TIME = 'change_time', 'Muốn đổi thời gian'
        PERSONAL_BUSY = 'personal_busy', 'Có việc bận cá nhân'
        WRONG_BOOKING = 'wrong_booking', 'Đặt nhầm dịch vụ/thời gian'
        NO_NEED = 'no_need', 'Không còn nhu cầu'
        OTHER = 'other', 'Lý do khác'

    class RefundStatus(models.TextChoices):
        NONE = 'none', 'Không cần hoàn tiền'
        PENDING = 'pending', 'Chờ admin hoàn tiền'
        REFUNDED = 'refunded', 'Đã hoàn tiền'

    class StaffServiceStatus(models.TextChoices):
        READY = 'ready', 'Sẵn sàng'
        SERVING = 'serving', 'Đang phục vụ'
        DONE = 'done', 'Đã phục vụ'
        REJECTED = 'rejected', 'Từ chối phục vụ'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name='Khách hàng',
    )

    service = models.ForeignKey(
        'services.Service',
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name='Dịch vụ',
    )

    full_name = models.CharField(
        max_length=255,
        verbose_name='Họ tên',
    )

    phone = models.CharField(
        max_length=20,
        verbose_name='Số điện thoại',
    )

    booking_date = models.DateField(
        verbose_name='Ngày đặt',
    )

    booking_time = models.TimeField(
        verbose_name='Giờ đặt',
    )

    guest_count = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Số lượng khách',
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings',
        verbose_name='Phòng phục vụ',
    )

    note = models.TextField(
        blank=True,
        verbose_name='Ghi chú',
    )

    addons = models.ManyToManyField(
        'services.ServiceAddon',
        blank=True,
        related_name='bookings',
        verbose_name='Dịch vụ thêm',
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name='Hình thức thanh toán',
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Trạng thái duyệt',
    )

    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_bookings',
        limit_choices_to={'is_staff': True},
        verbose_name='Nhân viên phục vụ',
    )

    staff_service_status = models.CharField(
        max_length=20,
        choices=StaffServiceStatus.choices,
        default=StaffServiceStatus.READY,
        verbose_name='Tình trạng phục vụ',
    )

    staff_reject_reason = models.TextField(
        blank=True,
        verbose_name='Lý do nhân viên từ chối',
    )

    staff_started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời gian bắt đầu phục vụ',
    )

    staff_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời gian phục vụ thành công',
    )

    staff_rejected_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời gian từ chối phục vụ',
    )

    cancel_reason = models.CharField(
        max_length=50,
        choices=CancelReason.choices,
        blank=True,
        null=True,
        verbose_name='Lý do hủy',
    )

    cancel_reason_other = models.TextField(
        blank=True,
        verbose_name='Lý do hủy khác',
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời gian hủy',
    )

    refund_status = models.CharField(
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.NONE,
        verbose_name='Trạng thái hoàn tiền',
    )

    refund_bank_name = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Ngân hàng hoàn tiền',
    )

    refund_account_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Số tài khoản hoàn tiền',
    )

    refund_account_name = models.CharField(
        max_length=160,
        blank=True,
        verbose_name='Tên chủ tài khoản hoàn tiền',
    )

    refunded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Thời gian hoàn tiền',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày tạo',
    )

    class Meta:
        ordering = ['-booking_date', '-booking_time']
        verbose_name = 'Lịch đặt'
        verbose_name_plural = 'Lịch đặt'

    def __str__(self):
        return f'{self.full_name} - {self.service.name}'

    def get_booking_datetime(self):
        booking_datetime = datetime.combine(
            self.booking_date,
            self.booking_time,
        )

        if timezone.is_naive(booking_datetime):
            booking_datetime = timezone.make_aware(
                booking_datetime,
                timezone.get_current_timezone(),
            )

        return booking_datetime

    def get_start_datetime(self):
        if not self.booking_date or not self.booking_time:
            return None

        return self.get_booking_datetime()

    def get_end_datetime(self):
        start_datetime = self.get_start_datetime()

        if start_datetime is None or not self.service_id:
            return None

        duration_minutes = getattr(
            self.service,
            'duration_minutes',
            60,
        ) or 60

        return start_datetime + timedelta(
            minutes=duration_minutes,
        )

    def is_time_overlap(self, other_booking):
        current_start = self.get_start_datetime()
        current_end = self.get_end_datetime()
        other_start = other_booking.get_start_datetime()
        other_end = other_booking.get_end_datetime()

        if not all([
            current_start,
            current_end,
            other_start,
            other_end,
        ]):
            return False

        return (
            current_start < other_end
            and current_end > other_start
        )

    def clean(self):
        super().clean()

        errors = {}

        if self.guest_count is not None and self.guest_count < 1:
            errors['guest_count'] = (
                'Số lượng khách phải lớn hơn hoặc bằng 1.'
            )

        if self.status != self.Status.CONFIRMED:
            if errors:
                raise ValidationError(errors)
            return

        if not self.room_id:
            errors['room'] = (
                'Khi duyệt lịch, bắt buộc phải chọn phòng.'
            )

        if not self.staff_id:
            errors['staff'] = (
                'Khi duyệt lịch, bắt buộc phải chọn nhân viên phục vụ.'
            )

        if errors:
            raise ValidationError(errors)

        if self.room.status != Room.Status.AVAILABLE:
            raise ValidationError({
                'room': 'Phòng hiện không sẵn sàng phục vụ.',
            })

        staff_bookings = (
            type(self).objects
            .filter(
                staff_id=self.staff_id,
                booking_date=self.booking_date,
                status=self.Status.CONFIRMED,
            )
            .exclude(pk=self.pk)
            .select_related('service')
        )

        for other_booking in staff_bookings:
            if self.is_time_overlap(other_booking):
                raise ValidationError({
                    'staff': 'Nhân viên không sẵn sàng phục vụ',
                })

        room_bookings = (
            type(self).objects
            .filter(
                room_id=self.room_id,
                booking_date=self.booking_date,
                status=self.Status.CONFIRMED,
            )
            .exclude(pk=self.pk)
            .select_related('service')
        )

        occupied_capacity = 0

        for other_booking in room_bookings:
            if self.is_time_overlap(other_booking):
                occupied_capacity += other_booking.guest_count or 1

        requested_capacity = self.guest_count or 1

        if occupied_capacity + requested_capacity > self.room.capacity:
            raise ValidationError({
                'room': 'Phòng đã đầy',
            })

    def is_expired(self):
        return self.get_booking_datetime() <= timezone.now()

    @classmethod
    def update_missed_bookings(cls):
        bookings = cls.objects.filter(
            status__in=[
                cls.Status.PENDING,
                cls.Status.PAID,
                cls.Status.CONFIRMED,
            ],
            staff_started_at__isnull=True,
            staff_completed_at__isnull=True,
        )

        for booking in bookings:
            if booking.is_expired():
                booking.status = cls.Status.MISSED
                booking.save(update_fields=['status'])

    def staff_name(self):
        if not self.staff:
            return ''

        try:
            if self.staff.profile.name:
                return self.staff.profile.name
        except Exception:
            pass

        if self.staff.get_full_name():
            return self.staff.get_full_name()

        return self.staff.username


class ServiceReview(models.Model):
    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='Lịch đặt',
    )

    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Dịch vụ',
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='service_reviews',
        verbose_name='Khách hàng',
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
        verbose_name='Số sao',
    )

    comment = models.TextField(
        blank=True,
        verbose_name='Nội dung đánh giá',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ngày đánh giá',
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Đánh giá dịch vụ'
        verbose_name_plural = 'Quản lý đánh giá dịch vụ'
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(rating__gte=1)
                    & models.Q(rating__lte=5)
                ),
                name='review_rating_from_1_to_5',
            ),
        ]

    def __str__(self):
        return f'{self.service.name} - {self.rating} sao'
