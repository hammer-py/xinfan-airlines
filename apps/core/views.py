from django.shortcuts import render

def home_view(request):
    latest_flights = []
    try:
        from apps.flights.models import Flight
        latest_flights = Flight.objects.select_related('created_by').order_by('-departure_time')[:6]
    except Exception:
        pass
    return render(request, 'core/home.html', {'latest_flights': latest_flights})

def about_view(request):
    return render(request, 'core/about.html')
