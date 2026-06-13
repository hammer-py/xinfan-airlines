from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Flight, FlightCrewSignup, PrivateFlightRequest
from apps.accounts.decorators import role_required
from apps.accounts.models import PREMIUM_ROLES, EMPLOYEE_ROLES

def flight_list_view(request):
    flights = Flight.objects.select_related('created_by').filter(is_private=False)
    can_see_private = (
        request.user.is_authenticated and (
            request.user.profile.role in PREMIUM_ROLES or
            request.user.profile.role in EMPLOYEE_ROLES or
            request.user.profile.role == 'admin'
        )
    )
    private_flights = Flight.objects.select_related('created_by').filter(is_private=True, status='scheduled') if can_see_private else Flight.objects.none()
    status = request.GET.get('status', '')
    route = request.GET.get('route', '')
    if status:
        flights = flights.filter(status=status)
        private_flights = private_flights.filter(status=status)
    if route:
        flights = flights.filter(route_type=route)
        private_flights = private_flights.filter(route_type=route)
    return render(request, 'flights/flight_list.html', {
        'flights': flights,
        'private_flights': private_flights,
    })

def flight_detail_view(request, pk):
    flight = get_object_or_404(Flight, pk=pk)

    if flight.is_private and (
        not request.user.is_authenticated or
        request.user.profile.role == 'economy'
    ):
        messages.error(request, '你没有权限查看此航班')
        return redirect('flight_list')

    signups = flight.crew_signups.select_related('user').all()
    user_signup = None
    applicant = None
    if request.user.is_authenticated:
        user_signup = flight.crew_signups.filter(user=request.user).first()
        if flight.is_private and hasattr(flight, 'source_request'):
            applicant = flight.source_request.user
    return render(request, 'flights/flight_detail.html', {
        'flight': flight, 'signups': signups, 'user_signup': user_signup,
        'applicant': applicant,
    })

@login_required
@role_required(['admin'])
def flight_create_view(request):
    if request.method == 'POST':
        try:
            flight = Flight.objects.create(
                flight_number=request.POST.get('flight_number', '').strip(),
                origin=request.POST.get('origin', '').strip(),
                destination=request.POST.get('destination', '').strip(),
                departure_time=request.POST.get('departure_time'),
                arrival_time=request.POST.get('arrival_time'),
                aircraft=request.POST.get('aircraft', 'Boeing 737-800').strip(),
                gate=request.POST.get('gate', '').strip() or None,
                route_type=request.POST.get('route_type', 'domestic'),
                status=request.POST.get('status', 'scheduled'),
                notes=request.POST.get('notes', '').strip() or None,
                created_by=request.user,
            )
            messages.success(request, f'航班 {flight.flight_number} 已创建')
            return redirect('flight_detail', flight.pk)
        except Exception as e:
            messages.error(request, f'创建失败: {e}')
    return render(request, 'flights/flight_form.html')

@login_required
@role_required(['admin'])
def flight_edit_view(request, pk):
    flight = get_object_or_404(Flight, pk=pk)
    if request.method == 'POST':
        flight.flight_number = request.POST.get('flight_number', flight.flight_number)
        flight.origin = request.POST.get('origin', flight.origin)
        flight.destination = request.POST.get('destination', flight.destination)
        flight.departure_time = request.POST.get('departure_time', flight.departure_time)
        flight.arrival_time = request.POST.get('arrival_time', flight.arrival_time)
        flight.aircraft = request.POST.get('aircraft', flight.aircraft)
        flight.gate = request.POST.get('gate', '').strip() or None
        flight.route_type = request.POST.get('route_type', flight.route_type)
        flight.status = request.POST.get('status', flight.status)
        flight.notes = request.POST.get('notes', '').strip() or None
        flight.save()
        messages.success(request, '航班已更新')
        return redirect('flight_detail', flight.pk)
    return render(request, 'flights/flight_form.html', {'flight': flight, 'editing': True})

@login_required
@role_required(['admin'])
def flight_delete_view(request, pk):
    flight = get_object_or_404(Flight, pk=pk)
    if request.method == 'POST':
        number = flight.flight_number
        flight.delete()
        messages.success(request, f'航班 {number} 已删除')
        return redirect('flight_list')
    return render(request, 'flights/flight_confirm_delete.html', {'flight': flight})

@login_required
@role_required(['employee', 'admin'])
def flight_signup_view(request, pk):
    flight = get_object_or_404(Flight, pk=pk)
    if request.method == 'POST':
        role = request.POST.get('role', '')
        if role not in dict(FlightCrewSignup.CREW_ROLES):
            messages.error(request, '请选择有效角色')
        else:
            signup, created = FlightCrewSignup.objects.get_or_create(
                flight=flight, user=request.user,
                defaults={'role': role}
            )
            if created:
                messages.success(request, '报名成功，等待管理员审批')
            else:
                messages.warning(request, '你已经报名过这个航班了')
        return redirect('flight_detail', flight.pk)
    return render(request, 'flights/flight_signup.html', {
        'flight': flight,
        'crew_roles': FlightCrewSignup.CREW_ROLES,
    })

@login_required
def my_signups_view(request):
    signups = FlightCrewSignup.objects.select_related('flight').filter(user=request.user).order_by('-signed_up_at')
    return render(request, 'flights/my_signups.html', {'signups': signups})

@login_required
@role_required(['admin'])
def admin_signups_view(request):
    signups = FlightCrewSignup.objects.select_related('flight', 'user').all().order_by('-signed_up_at')
    if request.method == 'POST':
        signup_id = request.POST.get('signup_id')
        action = request.POST.get('action')
        signup = get_object_or_404(FlightCrewSignup, id=signup_id)
        if action == 'approve':
            signup.status = 'approved'
        elif action == 'reject':
            signup.status = 'rejected'
        signup.save()
        messages.success(request, f'{signup.user.username} 的报名已更新')
        return redirect('admin_signups')
    return render(request, 'flights/admin_signups.html', {'signups': signups})


# ─── Private Flight Requests ──────────────────────────────

@login_required
def private_flight_request_view(request):
    if request.user.profile.role not in PREMIUM_ROLES:
        messages.error(request, '商务舱及以上等级用户才能申请私人航班')
        return redirect('home')

    if request.method == 'POST':
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
            return redirect('my_private_requests')

    return render(request, 'flights/private_flight_request.html', {
        'route_choices': Flight.ROUTE_CHOICES,
    })


@login_required
def my_private_requests_view(request):
    if request.user.profile.role not in PREMIUM_ROLES:
        messages.error(request, '商务舱及以上等级用户才能查看私人航班申请')
        return redirect('home')

    requests_list = PrivateFlightRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'flights/my_private_requests.html', {'requests': requests_list})


@login_required
@role_required(['admin'])
def admin_private_requests_view(request):
    requests_list = PrivateFlightRequest.objects.select_related('user', 'reviewed_by', 'created_flight').all().order_by('-created_at')

    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        req = get_object_or_404(PrivateFlightRequest, id=req_id)

        if action == 'approve':
            flight = Flight.objects.create(
                flight_number=req.flight_number,
                origin=req.origin, destination=req.destination,
                departure_time=req.departure_time, arrival_time=req.arrival_time,
                aircraft=req.aircraft, route_type=req.route_type,
                status='scheduled', is_private=True,
                notes=f'私人航班 — {req.user.username} 申请\n目的: {req.purpose}',
                created_by=req.user,
            )
            req.status = 'approved'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.created_flight = flight
            req.save()
            messages.success(request, f'已通过 {req.user.username} 的私人航班申请，航班 {req.flight_number} 已创建')

        elif action == 'reject':
            req.status = 'rejected'
            req.reviewed_by = request.user
            req.reviewed_at = timezone.now()
            req.review_note = request.POST.get('review_note', '').strip() or None
            req.save()
            messages.success(request, f'已拒绝 {req.user.username} 的私人航班申请')

        return redirect('admin_private_requests')

    status_filter = request.GET.get('status', '')
    if status_filter and status_filter in dict(PrivateFlightRequest.STATUS_CHOICES):
        requests_list = requests_list.filter(status=status_filter)

    return render(request, 'flights/admin_private_requests.html', {
        'requests': requests_list,
        'status_filter': status_filter,
    })
