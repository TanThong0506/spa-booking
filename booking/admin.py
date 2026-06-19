from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Booking, ServiceReview


class StaffChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        try:
            if obj.profile.name:
                return obj.profile.name
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

        User = get_user_model()

        self.fields['staff'] = StaffChoiceField(
            queryset=User.objects.filter(
                is_active=True,
                groups__name='Nhân viên'
            ).distinct(),
            required=False,
            label='Nhân viên phục vụ'
        )

    def clean(self):
        cleaned_data = super().clean()

        status = cleaned_data.get('status')
        staff = cleaned_data.get('staff')

        if status == Booking.Status.CONFIRMED and not staff:
            self.add_error(
                'staff',
                'Ở trạng thái "Đã được duyệt" bắt buộc phải chọn nhân viên phục vụ.'
            )

        return cleaned_data


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm

    list_display = [
        'full_name',
        'phone',
        'service',
        'booking_date',
        'booking_time',
        'payment_method',
        'status',
        'staff',
        'staff_service_status',
        'refund_status',
    ]

    list_filter = [
        'status',
        'payment_method',
        'staff',
        'staff_service_status',
        'refund_status',
        'booking_date',
        'service',
    ]

    search_fields = [
        'full_name',
        'phone',
        'service__name',
        'staff__username',
        'staff__first_name',
        'staff__last_name',
        'staff__profile__name',
        'staff_reject_reason',
    ]

    list_editable = [
        'status',
        'staff',
        'staff_service_status',
        'refund_status',
    ]

    filter_horizontal = [
        'addons',
    ]

    readonly_fields = [
        'created_at',
        'cancelled_at',
        'refunded_at',
        'staff_started_at',
        'staff_completed_at',
        'staff_rejected_at',
    ]

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
                'note',
                'created_at',
            )
        }),

        ('Admin duyệt dịch vụ', {
            'fields': (
                'payment_method',
                'status',
                'staff',
            )
        }),

        ('Tình trạng nhân viên phục vụ', {
            'fields': (
                'staff_service_status',
                'staff_reject_reason',
                'staff_started_at',
                'staff_completed_at',
                'staff_rejected_at',
            )
        }),

        ('Thông tin hủy lịch', {
            'fields': (
                'cancel_reason',
                'cancel_reason_other',
                'cancelled_at',
            )
        }),

        ('Thông tin hoàn tiền', {
            'fields': (
                'refund_status',
                'refund_bank_name',
                'refund_account_number',
                'refund_account_name',
                'refunded_at',
            )
        }),
    )

    ordering = [
        '-created_at',
    ]

    def get_queryset(self, request):
        Booking.update_missed_bookings()
        return super().get_queryset(request)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'staff':
            User = get_user_model()

            return StaffChoiceField(
                queryset=User.objects.filter(
                    is_active=True,
                    groups__name='Nhân viên'
                ).distinct(),
                required=False,
                label='Nhân viên phục vụ'
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def save_model(self, request, obj, form, change):
        if obj.status == Booking.Status.CONFIRMED and obj.staff:
            if obj.staff_service_status not in [
                Booking.StaffServiceStatus.SERVING,
                Booking.StaffServiceStatus.DONE,
                Booking.StaffServiceStatus.REJECTED,
            ]:
                obj.staff_service_status = Booking.StaffServiceStatus.READY

        if obj.refund_status == Booking.RefundStatus.REFUNDED and obj.refunded_at is None:
            obj.refunded_at = timezone.now()

        if obj.staff_service_status == Booking.StaffServiceStatus.SERVING and obj.staff_started_at is None:
            obj.staff_started_at = timezone.now()

        if obj.staff_service_status == Booking.StaffServiceStatus.DONE:
            obj.status = Booking.Status.COMPLETED

            if obj.staff_completed_at is None:
                obj.staff_completed_at = timezone.now()

        if obj.staff_service_status == Booking.StaffServiceStatus.REJECTED and obj.staff_rejected_at is None:
            obj.staff_rejected_at = timezone.now()

        super().save_model(request, obj, form, change)


class ServiceReviewAdminForm(forms.ModelForm):
    class Meta:
        model = ServiceReview
        fields = [
            'booking',
            'rating',
            'comment',
        ]

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')

        if rating is None:
            raise forms.ValidationError('Vui lòng nhập số sao đánh giá.')

        if rating < 1 or rating > 5:
            raise forms.ValidationError('Số sao đánh giá chỉ được từ 1 đến 5.')

        return rating


@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    form = ServiceReviewAdminForm

    list_display = [
        'booking',
        'service',
        'user',
        'rating_stars',
        'comment_short',
        'created_at',
    ]

    list_filter = [
        'rating',
        'service',
        'created_at',
    ]

    search_fields = [
        'comment',
        'service__name',
        'user__username',
        'user__first_name',
        'user__last_name',
        'booking__full_name',
        'booking__phone',
    ]

    readonly_fields = [
        'service',
        'user',
        'created_at',
    ]

    fields = [
        'booking',
        'service',
        'user',
        'rating',
        'comment',
        'created_at',
    ]

    ordering = [
        '-created_at',
    ]

    def save_model(self, request, obj, form, change):
        if obj.booking:
            obj.service = obj.booking.service
            obj.user = obj.booking.user

        super().save_model(request, obj, form, change)

    def rating_stars(self, obj):
        return '★' * obj.rating + '☆' * (5 - obj.rating)

    rating_stars.short_description = 'Đánh giá'

    def comment_short(self, obj):
        if not obj.comment:
            return 'Không có nội dung'

        if len(obj.comment) > 60:
            return obj.comment[:60] + '...'

        return obj.comment

    comment_short.short_description = 'Nội dung'