from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import UserProfile
from .decorators import role_required

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        errors = []
        if not username or not email or not password:
            errors.append('请填写所有必填字段')
        if len(username) < 2:
            errors.append('用户名至少 2 个字符')
        if len(password) < 6:
            errors.append('密码至少 6 个字符')
        if password != confirm_password:
            errors.append('两次输入的密码不一致')
        if User.objects.filter(username=username).exists():
            errors.append('用户名已存在')
        if User.objects.filter(email=email).exists():
            errors.append('邮箱已被注册')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'accounts/register.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        messages.success(request, f'欢迎加入新帆航空，{username}！')
        return redirect('home')

    return render(request, 'accounts/register.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'欢迎回来，{user.username}！')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, '用户名或密码错误')

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, '已退出登录')
    return redirect('home')

@login_required
def profile_view(request):
    profile = request.user.profile
    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def profile_edit_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        profile.phone = request.POST.get('phone', '').strip() or None
        profile.bio = request.POST.get('bio', '').strip() or None
        profile.save()
        messages.success(request, '资料已更新')
        return redirect('profile')
    return render(request, 'accounts/profile_edit.html', {'profile': profile})

# ─── Admin Panel ────────────────────────────────────────────

@login_required
@role_required(['admin'])
def admin_panel_view(request):
    total_users = User.objects.count()
    total_flights = 0  # will be set by flights app
    pending_signups = 0
    pending_applications = 0
    try:
        from apps.flights.models import Flight, FlightCrewSignup
        total_flights = Flight.objects.count()
        pending_signups = FlightCrewSignup.objects.filter(status='pending').count()
    except Exception:
        pass
    try:
        from apps.recruitment.models import JobApplication
        pending_applications = JobApplication.objects.filter(status='pending').count()
    except Exception:
        pass

    ctx = {
        'total_users': total_users,
        'total_flights': total_flights,
        'pending_signups': pending_signups,
        'pending_applications': pending_applications,
    }
    return render(request, 'accounts/admin_panel.html', ctx)

@login_required
@role_required(['admin'])
def admin_users_view(request):
    users = User.objects.select_related('profile').all().order_by('-date_joined')
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_role = request.POST.get('role')
        target = get_object_or_404(User, id=user_id)
        if new_role in dict(UserProfile.ROLE_CHOICES):
            target.profile.role = new_role
            target.profile.save()
            messages.success(request, f'{target.username} 的角色已更新为 {target.profile.get_role_display()}')
        return redirect('admin_users')
    return render(request, 'accounts/admin_users.html', {'users': users})
