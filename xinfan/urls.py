from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('flights/', include('apps.flights.urls')),
    path('mileage/', include('apps.mileage.urls')),
    path('recruitment/', include('apps.recruitment.urls')),
]
