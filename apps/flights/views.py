from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Flight, FlightCrewSignup
from apps.accounts.decorators import role_required

def flight_list_view(request):
    flights = Flight.objects.select_related('created_by').all()
    # Filtering
    status = request.GET.get('status', '')
    route = request.GET.get('route', '')
    if status:
        flights = flights.filter(status=status)
    if route:
        flights = flights.filter(route_type=route)
    return render(request, 'flights/flight_list.html', {'flights': flights})

def flight_detail_view(request, pk):
    flight = get_object_or_404(Flight, pk=pk)
    signups = flight.crew_signups.select_related('user').all()
    user_signup = None
    if request.user.is_authenticated:
        user_signup = flight.crew_signups.filter(user=request.user).first()
    return render(request, 'flights/flight_detail.html', {
        'flight': flight, 'signups': signups, 'user_signup': user_signup
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
                aircraft=request.POST.get('aircraft', 'A320neo').strip(),
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
