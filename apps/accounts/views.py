from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import transaction
from django.utils.decorators import method_decorator
from .models import UserProfile, ROLE_CHOICES
from .decorators import role_required
import json
import urllib.request

TURNSTILE_SECRET = '0x4AAAAAADnKlcEsR3ju3SUhf65od20RxUU'


def _verify_turnstile(token):
    if not token:
        return False
    data = json.dumps({'secret': TURNSTILE_SECRET, 'response': token}).encode()
    req = urllib.request.Request(
        'https://challenges.cloudflare.com/turnstile/v0/siteverify',
        data=data, headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode()).get('success', False)
    except Exception:
        return False


def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        turnstile_token = request.POST.get('cf-turnstile-response', '')

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
        if not _verify_turnstile(turnstile_token):
            errors.append('人机验证失败，请重试')

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
        turnstile_token = request.POST.get('cf-turnstile-response', '')

        if not _verify_turnstile(turnstile_token):
            messages.error(request, '人机验证失败，请重试')
            return render(request, 'accounts/login.html')

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
    total_flights = 0
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
@staff_member_required(login_url='login')
def admin_users_view(request):
    role_choices = dict(ROLE_CHOICES)

    search_query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '')

    users = User.objects.select_related('profile').all()
    if search_query:
        users = users.filter(
            username__icontains=search_query
        ) | users.filter(email__icontains=search_query)
        users = users.distinct()
    if role_filter and role_filter in role_choices:
        users = users.filter(profile__role=role_filter)
    users = users.order_by('-date_joined')

    if request.method == 'POST':
        action = request.POST.get('action', 'update_role')

        if action == 'create_user':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password', '')
            target_role = request.POST.get('role', 'economy')

            errors = []
            if not username or not email or not password:
                errors.append('请填写所有必填字段')
            if len(username) < 2:
                errors.append('用户名至少 2 个字符')
            if len(password) < 6:
                errors.append('密码至少 6 个字符')
            if User.objects.filter(username=username).exists():
                errors.append('用户名已存在')
            if User.objects.filter(email=email).exists():
                errors.append('邮箱已被注册')
            if target_role not in role_choices:
                errors.append('无效的角色')

            if errors:
                for e in errors:
                    messages.error(request, e)
            else:
                with transaction.atomic():
                    user = User.objects.create_user(username=username, email=email, password=password)
                    user.profile.role = target_role
                    user.profile.save()
                messages.success(request, f'用户 {username} 创建成功（{role_choices[target_role]}）')
            return redirect('admin_users')

        if action == 'delete_user':
            target = get_object_or_404(User, id=request.POST.get('user_id'))
            if target == request.user:
                messages.error(request, '不能删除自己的账户')
            else:
                username = target.username
                target.delete()
                messages.success(request, f'用户 {username} 已删除')
            return redirect('admin_users')

        if action == 'update_role':
            target = get_object_or_404(User, id=request.POST.get('user_id'))
            new_role = request.POST.get('role')
            if new_role in role_choices:
                if not hasattr(target, 'profile'):
                    UserProfile.objects.create(user=target)
                target.profile.role = new_role
                target.profile.save()
                messages.success(request, f'{target.username} 的角色已更新为 {target.profile.get_role_display()}')
            return redirect('admin_users')

        if action == 'batch_update_role':
            user_ids = request.POST.getlist('user_ids')
            new_role = request.POST.get('role')
            if not user_ids:
                messages.warning(request, '请先选择用户')
            elif new_role not in role_choices:
                messages.error(request, '无效的角色')
            else:
                count = 0
                for user in User.objects.filter(id__in=user_ids).exclude(id=request.user.id):
                    if not hasattr(user, 'profile'):
                        UserProfile.objects.create(user=user)
                    user.profile.role = new_role
                    user.profile.save()
                    count += 1
                messages.success(request, f'已将 {count} 个用户的角色更新为 {role_choices[new_role]}')
            return redirect('admin_users')

        if action == 'batch_delete':
            user_ids = request.POST.getlist('user_ids')
            if not user_ids:
                messages.warning(request, '请先选择用户')
            else:
                qs = User.objects.filter(id__in=user_ids).exclude(id=request.user.id)
                count = qs.count()
                qs.delete()
                messages.success(request, f'已删除 {count} 个用户')
            return redirect('admin_users')

    ctx = {
        'users': users,
        'role_choices': ROLE_CHOICES,
        'search_query': search_query,
        'role_filter': role_filter,
    }
    return render(request, 'accounts/admin_users.html', ctx)
