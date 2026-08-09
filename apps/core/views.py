from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages

VIP_CLUB_ROLES = {'business', 'first_class', 'investor', 'uinv', 'admin'}


def hkhos_demo_view(request):
    return render(request, 'core/hkhos_demo.html')


def vip_club_view(request):
    if not request.user.is_authenticated or request.user.profile.role not in VIP_CLUB_ROLES:
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

            req.flight_number = request.POST.get('flight_number', '').strip()
            req.origin = request.POST.get('origin', '').strip()
            req.destination = request.POST.get('destination', '').strip()
            req.departure_time = request.POST.get('departure_time', req.departure_time)
            req.arrival_time = request.POST.get('arrival_time', req.arrival_time)
            req.aircraft = request.POST.get('aircraft', '').strip()
            req.route_type = request.POST.get('route_type', 'domestic')
            req.purpose = request.POST.get('purpose', '').strip()
            req.passenger_count = int(request.POST.get('passenger_count', 1))
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
        passenger_count = request.POST.get('passenger_count', '1')
        notes = request.POST.get('notes', '').strip() or None

        if not all([flight_number, origin, destination, departure_time, arrival_time, purpose]):
            messages.error(request, '请填写所有必填字段')
        elif Flight.objects.filter(flight_number=flight_number).exists():
            messages.error(request, '该航班号已存在')
        else:
            PrivateFlightRequest.objects.create(
                user=request.user,
                flight_number=flight_number, origin=origin, destination=destination,
                departure_time=departure_time, arrival_time=arrival_time,
                aircraft=aircraft, route_type=route_type,
                purpose=purpose, passenger_count=int(passenger_count), notes=notes,
            )
            messages.success(request, '私人航班申请已提交，请等待管理员审批')
            return redirect('vip_club')

    return render(request, 'core/vip_club.html', {
        'requests': requests_list,
        'route_choices': Flight.ROUTE_CHOICES,
    })


def verify_txt(request):
    return HttpResponse('7d13c19ea2635efa621af4db13ff59f9e04643ff', content_type='text/plain')

def home_view(request):
    latest_flights = []
    try:
        from apps.flights.models import Flight
        from apps.accounts.models import PREMIUM_ROLES, EMPLOYEE_ROLES
        qs = Flight.objects.select_related('created_by').order_by('-departure_time')
        if not request.user.is_authenticated or request.user.profile.role == 'economy':
            qs = qs.filter(is_private=False)
        latest_flights = qs[:6]
    except Exception:
        pass
    return render(request, 'core/home.html', {'latest_flights': latest_flights})

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
