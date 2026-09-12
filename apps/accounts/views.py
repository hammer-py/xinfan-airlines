from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from .models import UserProfile, ROLE_CHOICES, ADMIN_ROLES
from .decorators import role_required
import json
import urllib.request


def _safe_next_url(request):
    """只允许跳转到本站地址，避免开放重定向。"""
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return next_url
    return reverse('home')


def _verify_turnstile(token):
    secret = settings.TURNSTILE_SECRET_KEY
    if not token:
        return False
    if not secret:
        # 未配置密钥时不能放行，否则人机验证形同虚设
        return False
    data = json.dumps({'secret': secret, 'response': token}).encode()
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

    next_url = request.POST.get('next') or request.GET.get('next') or ''

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        turnstile_token = request.POST.get('cf-turnstile-response', '')

        if not _verify_turnstile(turnstile_token):
            messages.error(request, '人机验证失败，请重试')
            return render(request, 'accounts/login.html', {'next': next_url})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'欢迎回来，{user.username}！')
            return redirect(_safe_next_url(request))
        else:
            messages.error(request, '用户名或密码错误')

    return render(request, 'accounts/login.html', {'next': next_url})


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

        # QQ 号同步头像
        qq_number = request.POST.get('qq_number', '').strip() or None
        if qq_number != profile.qq_number:
            profile.qq_number = qq_number
            # 设置 QQ 号时清除自定义头像
            if qq_number:
                profile.avatar = None

        # 自定义头像上传
        avatar_file = request.FILES.get('avatar')
        if avatar_file:
            # 验证文件类型
            if not avatar_file.content_type.startswith('image/'):
                messages.error(request, '<span class="lang-zh">仅支持图片文件</span><span class="lang-en">Only image files are supported</span>')
                return render(request, 'accounts/profile_edit.html', {'profile': profile})
            if avatar_file.size > 2 * 1024 * 1024:
                messages.error(request, '<span class="lang-zh">图片大小不能超过 2MB</span><span class="lang-en">Image size must be under 2MB</span>')
                return render(request, 'accounts/profile_edit.html', {'profile': profile})
            profile.avatar = avatar_file
            # 上传自定义头像时清除 QQ 号
            profile.qq_number = None

        # 清除头像
        if request.POST.get('clear_avatar') == '1':
            profile.avatar = None
            profile.qq_number = None

        profile.save()
        messages.success(request, '<span class="lang-zh">资料已更新</span><span class="lang-en">Profile updated</span>')
        return redirect('profile')
    return render(request, 'accounts/profile_edit.html', {'profile': profile})


# ─── Admin Panel ────────────────────────────────────────────

@login_required
@role_required(['staff'])
def admin_panel_view(request):
    from apps.flights.models import Flight, FlightCrewSignup
    from apps.recruitment.models import JobApplication

    total_users = User.objects.count()
    total_flights = Flight.objects.count()
    pending_signups = FlightCrewSignup.objects.filter(status='pending').count()
    pending_applications = JobApplication.objects.filter(status='pending').count()

    is_full_admin = request.user.profile.role in ADMIN_ROLES
    ctx = {
        'total_users': total_users,
        'total_flights': total_flights,
        'pending_signups': pending_signups,
        'pending_applications': pending_applications,
        'is_full_admin': is_full_admin,
    }
    return render(request, 'accounts/admin_panel.html', ctx)


@login_required
def admin_users_view(request):
    if request.user.profile.role not in ADMIN_ROLES:
        messages.error(request, '你没有权限访问此页面')
        return redirect('home')

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
                profile, _ = UserProfile.objects.get_or_create(user=target)
                profile.role = new_role
                profile.save()
                messages.success(request, f'{target.username} 的角色已更新为 {profile.get_role_display()}')
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
                    profile, _ = UserProfile.objects.get_or_create(user=user)
                    profile.role = new_role
                    profile.save()
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
