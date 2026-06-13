from django.shortcuts import render
from django.http import HttpResponse

def verify_txt(request):
    return HttpResponse('7d13c19ea2635efa621af4db13ff59f9e04643\nff', content_type='text/plain')

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
