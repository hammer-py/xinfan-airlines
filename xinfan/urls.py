from django.contrib import admin
from django.urls import path, include
from apps.core.views import verify_txt

urlpatterns = [
    path('5245070195fc163a6d7e3927ecac8193.txt', verify_txt),
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('flights/', include('apps.flights.urls')),
    path('mileage/', include('apps.mileage.urls')),
    path('recruitment/', include('apps.recruitment.urls')),
]
