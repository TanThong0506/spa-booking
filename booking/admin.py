from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Booking, Room, ServiceReview


class StaffChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        try:
            profile_name = obj.profile.name
            if profile_name:
                return profile_name
        except Exception:
            pass

        full_name = obj.get_full_name()
        if full_name:
            return full_name

        return f'Chưa nhập tên - {obj.username}'


class BookingAdminForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_model = get_user_model()

        staff_queryset = (
            user_model.objects
            .filter(
                is_active=True,
                groups__name='Nhân viên',
            )
            .distinct()
            .order_by('first_name', 'last_name', 'username')
        )

        self.fields['staff'] = StaffChoiceField(
            queryset=staff_queryset,
            required=False,
            label='Nhân viên phục vụ',
        )

        self.fields['room'].queryset = (
            Room.objects
            .all()
            .order_by('name')
        )

    def clean(self):
        cleaned_data = super().clean()

        status = cleaned_data.get('status')
        room = cleaned_data.get('room')
        staff = cleaned_data.get('staff')
        staff_service_status = cleaned_data.get(
            'staff_service_status'
        )

        # Khi nhân viên bắt đầu hoặc hoàn tất phục vụ,
        # xem lịch như đang được duyệt để model kiểm tra trùng lịch.
        if staff_service_status in [
            Booking.StaffServiceStatus.SERVING,
            Booking.StaffServiceStatus.DONE,
        ]:
            cleaned_data['status'] = Booking.Status.CONFIRMED
            status = Booking.Status.CONFIRMED

        assignment_required = status in [
            Booking.Status.CONFIRMED,
            Booking.Status.COMPLETED,
        ]

        if assignment_required and not room:
            self.add_error(
                'room',
                'Ở trạng thái "Đã được duyệt" bắt buộc phải chọn phòng.',
            )

        if assignment_required and not staff:
            self.add_error(
                'staff',
                (
                    'Ở trạng thái "Đã được duyệt" bắt buộc phải '
                    'chọn nhân viên phục vụ.'
                ),
            )

        if (
            assignment_required
            and room
            and room.status != Room.Status.AVAILABLE
        ):
            self.add_error(
                'room',
                'Phòng hiện không sẵn sàng phục vụ.',
            )

        return cleaned_data


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'capacity',
        'status',
        'updated_at',
    )

    list_filter = (
        'status',
    )

    search_fields = (
        'name',
        'description',
    )

    list_editable = (
        'capacity',
        'status',
    )

    ordering = (
        'name',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    fieldsets = (
        ('Thông tin phòng', {
            'fields': (
                'name',
                'capacity',
                'status',
                'description',
            ),
        }),
        ('Thời gian', {
            'fields': (
                'created_at',
                'updated_at',
            ),
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm

    list_display = (
        'full_name',
        'phone',
        'service',
        'booking_date',
        'booking_time',
        'guest_count',
        'room',
        'payment_method',
        'status',
        'staff',
        'staff_service_status',
        'refund_status',
    )

    list_filter = (
        'status',
        'payment_method',
        'room',
        'staff',
        'staff_service_status',
        'refund_status',
        'booking_date',
        'service',
    )

    search_fields = (
        'full_name',
        'phone',
        'service__name',
        'room__name',
        'staff__username',
        'staff__first_name',
        'staff__last_name',
        'staff__profile__name',
        'staff_reject_reason',
    )

    list_editable = (
        'room',
        'status',
        'staff',
        'staff_service_status',
        'refund_status',
    )

    filter_horizontal = (
        'addons',
    )

    readonly_fields = (
        'created_at',
        'cancelled_at',
        'refunded_at',
        'staff_started_at',
        'staff_completed_at',
        'staff_rejected_at',
    )

    fieldsets = (
        ('Thông tin đặt lịch', {
            'fields': (
                'user',
                'service',
                'addons',
                'full_name',
                'phone',
                'booking_date',
                'booking_time',
                'guest_count',
                'note',
                'created_at',
            ),
        }),

        ('Admin duyệt lịch', {
            'fields': (
                'payment_method',
                'status',
                'room',
                'staff',
            ),
            'description': (
                'Khi chuyển lịch sang "Đã được duyệt", '
                'bắt buộc phải chọn phòng và nhân viên phục vụ.'
            ),
        }),

        ('Tình trạng nhân viên phục vụ', {
            'fields': (
                'staff_service_status',
                'staff_reject_reason',
                'staff_started_at',
                'staff_completed_at',
                'staff_rejected_at',
            ),
        }),

        ('Thông tin hủy lịch', {
            'fields': (
                'cancel_reason',
                'cancel_reason_other',
                'cancelled_at',
            ),
        }),

        ('Thông tin hoàn tiền', {
            'fields': (
                'refund_status',
                'refund_bank_name',
                'refund_account_number',
                'refund_account_name',
                'refunded_at',
            ),
        }),
    )

    ordering = (
        '-created_at',
    )

    list_select_related = (
        'service',
        'room',
        'staff',
        'user',
    )

    def get_queryset(self, request):
        Booking.update_missed_bookings()

        return (
            super()
            .get_queryset(request)
            .select_related(
                'service',
                'room',
                'staff',
                'user',
            )
        )

    def save_model(self, request, obj, form, change):
        if (
            obj.status == Booking.Status.CONFIRMED
            and obj.staff
            and obj.staff_service_status not in [
                Booking.StaffServiceStatus.SERVING,
                Booking.StaffServiceStatus.DONE,
                Booking.StaffServiceStatus.REJECTED,
            ]
        ):
            obj.staff_service_status = (
                Booking.StaffServiceStatus.READY
            )

        if (
            obj.refund_status == Booking.RefundStatus.REFUNDED
            and obj.refunded_at is None
        ):
            obj.refunded_at = timezone.now()

        if (
            obj.staff_service_status
            == Booking.StaffServiceStatus.SERVING
            and obj.staff_started_at is None
        ):
            obj.staff_started_at = timezone.now()

        if (
            obj.staff_service_status
            == Booking.StaffServiceStatus.DONE
        ):
            obj.status = Booking.Status.COMPLETED

            if obj.staff_completed_at is None:
                obj.staff_completed_at = timezone.now()

        if (
            obj.staff_service_status
            == Booking.StaffServiceStatus.REJECTED
            and obj.staff_rejected_at is None
        ):
            obj.staff_rejected_at = timezone.now()

        super().save_model(request, obj, form, change)


class ServiceReviewAdminForm(forms.ModelForm):
    class Meta:
        model = ServiceReview
        fields = (
            'booking',
            'rating',
            'comment',
        )

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')

        if rating is None:
            raise forms.ValidationError(
                'Vui lòng nhập số sao đánh giá.'
            )

        if rating < 1 or rating > 5:
            raise forms.ValidationError(
                'Số sao đánh giá chỉ được từ 1 đến 5.'
            )

        return rating


@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    form = ServiceReviewAdminForm

    list_display = (
        'booking',
        'service',
        'user',
        'rating_stars',
        'comment_short',
        'created_at',
    )

    list_filter = (
        'rating',
        'service',
        'created_at',
    )

    search_fields = (
        'comment',
        'service__name',
        'user__username',
        'user__first_name',
        'user__last_name',
        'booking__full_name',
        'booking__phone',
    )

    readonly_fields = (
        'service',
        'user',
        'created_at',
    )

    fields = (
        'booking',
        'service',
        'user',
        'rating',
        'comment',
        'created_at',
    )

    ordering = (
        '-created_at',
    )

    list_select_related = (
        'booking',
        'service',
        'user',
    )

    def save_model(self, request, obj, form, change):
        if obj.booking:
            obj.service = obj.booking.service
            obj.user = obj.booking.user

        super().save_model(request, obj, form, change)

    @admin.display(description='Đánh giá')
    def rating_stars(self, obj):
        return '★' * obj.rating + '☆' * (5 - obj.rating)

    @admin.display(description='Nội dung')
    def comment_short(self, obj):
        if not obj.comment:
            return 'Không có nội dung'

        if len(obj.comment) > 60:
            return obj.comment[:60] + '...'

        return obj.comment
