from django.shortcuts import render

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
    return render(request, 'core/about.html')
