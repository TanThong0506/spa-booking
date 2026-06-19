from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect, render

from .models import UserProfile


def get_redirect_by_role(user):
    if user.is_superuser:
        return 'admin:index'

    if user.groups.filter(name='Nhân viên').exists():
        return 'staff:dashboard'

    return 'home'


def get_user_display_name(user):
    try:
        if user.profile.name:
            return user.profile.name
    except Exception:
        pass

    if user.get_full_name():
        return user.get_full_name()

    return user.username


def logout_view(request):
    logout(request)
    return redirect('home')


def register_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()

        if not name or not phone or not email or not password1 or not password2:
            messages.error(request, 'Vui lòng nhập đầy đủ thông tin.')
            return redirect('accounts:register')

        if password1 != password2:
            messages.error(request, 'Mật khẩu nhập lại không khớp.')
            return redirect('accounts:register')

        if len(password1) < 6:
            messages.error(request, 'Mật khẩu phải có ít nhất 6 ký tự.')
            return redirect('accounts:register')

        if User.objects.filter(username=phone).exists():
            messages.error(request, 'Số điện thoại này đã được đăng ký.')
            return redirect('accounts:register')

        if UserProfile.objects.filter(phone=phone).exists():
            messages.error(request, 'Số điện thoại này đã được đăng ký.')
            return redirect('accounts:register')

        try:
            user = User.objects.create_user(
                username=phone,
                email=email,
                password=password1
            )

            UserProfile.objects.create(
                user=user,
                phone=phone,
                name=name,
                email=email
            )

            customer_group, created = Group.objects.get_or_create(name='Khách hàng')
            user.groups.add(customer_group)

            user.is_staff = False
            user.is_superuser = False
            user.is_active = True
            user.save()

            messages.success(request, 'Đăng ký thành công! Vui lòng đăng nhập.')
            return redirect('accounts:login')

        except Exception as e:
            messages.error(request, f'Lỗi: {str(e)}')
            return redirect('accounts:register')

    return render(request, 'account/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect(get_redirect_by_role(request.user))

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(
            request,
            username=phone,
            password=password
        )

        if user is not None:
            if not user.is_active:
                messages.error(request, 'Tài khoản của bạn đã bị khóa.')
                return render(request, 'account/login.html')

            login(request, user)

            display_name = get_user_display_name(user)
            messages.success(request, f'Chào mừng {display_name}! Đăng nhập thành công.')

            return redirect(get_redirect_by_role(user))

        messages.error(request, 'Số điện thoại hoặc mật khẩu không đúng.')

    return render(request, 'account/login.html')