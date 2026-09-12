from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.accounts.models import PREMIUM_ROLES


def _parse_int(value, default=1, minimum=1):
    """安全地把表单字符串转成整数，非法输入回退到默认值。"""
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return max(number, minimum)


def _parse_dt(value):
    """把 datetime-local 表单值解析为当前时区的 aware datetime。

    USE_TZ=True 时，naive datetime 会被当作 UTC 直接写库，
    导致用户输入的本地时间在页面上偏移 8 小时（Asia/Shanghai）。
    """
    if not value:
        return None
    if hasattr(value, 'tzinfo'):
        return value if timezone.is_aware(value) else timezone.make_aware(value)
    text = str(value).strip().replace('T', ' ')
    parsed = parse_datetime(text)
    if parsed is None:
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
            try:
                parsed = timezone.datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
    if parsed is None:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _profile_role(request):
    profile = getattr(request.user, 'profile', None)
    return getattr(profile, 'role', None)


def hkhos_demo_view(request):
    """旧版首页设计稿，仅管理员/高舱用户（或本地开发）可访问。"""
    if not settings.DEBUG and _profile_role(request) not in PREMIUM_ROLES:
        messages.error(request, '页面不存在')
        return redirect('home')
    return render(request, 'core/hkhos_demo.html')


def vip_club_view(request):
    if (
        not request.user.is_authenticated
        or getattr(getattr(request.user, 'profile', None), 'role', None) not in PREMIUM_ROLES
    ):
        messages.error(request, '仅商务舱及以上等级用户可访问')
        return redirect('home')

    from apps.flights.models import PrivateFlightRequest, Flight
    requests_list = PrivateFlightRequest.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action', 'create')

        # ── Edit & resubmit ────────────────────────────
        if action == 'edit_request':
            req_id = request.POST.get('request_id')
            req = PrivateFlightRequest.objects.filter(id=req_id, user=request.user).first()
            if not req or req.status not in ('rejected', 'approved'):
                messages.error(request, '无法修改该申请')
                return redirect('vip_club')

            flight_number = request.POST.get('flight_number', '').strip()
            if not flight_number:
                messages.error(request, '航班号不能为空')
                return redirect('vip_club')
            if Flight.objects.filter(flight_number=flight_number).exclude(
                pk=req.created_flight_id
            ).exists():
                messages.error(request, '该航班号已存在')
                return redirect('vip_club')

            req.flight_number = flight_number
            req.origin = request.POST.get('origin', '').strip()
            req.destination = request.POST.get('destination', '').strip()
            req.departure_time = _parse_dt(request.POST.get('departure_time')) or req.departure_time
            req.arrival_time = _parse_dt(request.POST.get('arrival_time')) or req.arrival_time
            req.aircraft = request.POST.get('aircraft', '').strip()
            req.route_type = request.POST.get('route_type', 'domestic')
            req.purpose = request.POST.get('purpose', '').strip()
            req.passenger_count = _parse_int(request.POST.get('passenger_count'), default=1)
            req.notes = request.POST.get('notes', '').strip() or None

            if req.created_flight:
                req.created_flight.delete()
                req.created_flight = None
            req.status = 'pending'
            req.reviewed_by = None
            req.reviewed_at = None
            req.review_note = '用户修改后重新提交审核'
            req.save()
            messages.success(request, '申请已修改并重新提交审核')
            return redirect('vip_club')

        # ── Create new ─────────────────────────────────
        flight_number = request.POST.get('flight_number', '').strip()
        origin = request.POST.get('origin', '').strip()
        destination = request.POST.get('destination', '').strip()
        departure_time = request.POST.get('departure_time', '')
        arrival_time = request.POST.get('arrival_time', '')
        aircraft = request.POST.get('aircraft', 'Gulf Stream 650').strip()
        route_type = request.POST.get('route_type', 'domestic')
        purpose = request.POST.get('purpose', '').strip()
        passenger_count = _parse_int(request.POST.get('passenger_count'), default=1)
        notes = request.POST.get('notes', '').strip() or None

        if not all([flight_number, origin, destination, departure_time, arrival_time, purpose]):
            messages.error(request, '请填写所有必填字段')
        elif Flight.objects.filter(flight_number=flight_number).exists():
            messages.error(request, '该航班号已存在')
        else:
            departure_dt = _parse_dt(departure_time)
            arrival_dt = _parse_dt(arrival_time)
            if not departure_dt or not arrival_dt:
                messages.error(request, '请填写有效的计划起飞/到达时间')
                return redirect('vip_club')
            PrivateFlightRequest.objects.create(
                user=request.user,
                flight_number=flight_number, origin=origin, destination=destination,
                departure_time=departure_dt, arrival_time=arrival_dt,
                aircraft=aircraft, route_type=route_type,
                purpose=purpose, passenger_count=passenger_count, notes=notes,
            )
            messages.success(request, '私人航班申请已提交，请等待管理员审批')
            return redirect('vip_club')

    return render(request, 'core/vip_club.html', {
        'requests': requests_list,
        'route_choices': Flight.ROUTE_CHOICES,
    })


def verify_txt(request):
    """站点归属校验文件。

    只返回校验串，不要在此处追加任何密钥/订阅地址：
    该路径是公开可读的，写进来的内容等同于公开发布。
    """
    return HttpResponse('7d13c19ea2635efa621af4db13ff59f9e04643ff', content_type='text/plain')

def home_view(request):
    from apps.flights.models import Flight

    qs = Flight.objects.select_related('created_by').order_by('-departure_time')
    if not request.user.is_authenticated or request.user.profile.role == 'economy':
        qs = qs.filter(is_private=False)
    return render(request, 'core/home.html', {'latest_flights': qs[:6]})

def about_view(request):
    main_fleet = [
        'Boeing 737-100', 'Boeing 737-800', 'Boeing 757-300',
        'Boeing 787-10', 'Boeing 747-200',
        'Airbus 318 CEO', 'Airbus 220-300', 'Airbus 321CEO',
        'Airbus 350-900', 'Airbus 320CEO',
        'DCH-6', 'Concorde', 'EMB-120',
    ]
    private_fleet = [
        'Gulf Stream 650', 'Airbus 319 ACJ', 'Boeing 787-10',
        'Falcon 7x', 'KingC90', 'PC-12',
    ]
    future_fleet = ['B777 300ER', 'A380']
    maintenance_fleet = ['A340', 'A330', 'E175']
    return render(request, 'core/about.html', {
        'main_fleet': main_fleet,
        'private_fleet': private_fleet,
        'future_fleet': future_fleet,
        'maintenance_fleet': maintenance_fleet,
    })


def error_404_view(request, exception=None):
    return render(request, '404.html', status=404)


def error_500_view(request):
    return render(request, '500.html', status=500)
