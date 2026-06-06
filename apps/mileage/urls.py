from django.urls import path
from . import views

urlpatterns = [
    path('', views.mileage_list_view, name='mileage_list'),
    path('redeem/', views.mileage_redeem_view, name='mileage_redeem'),
    path('grant/', views.mileage_grant_view, name='mileage_grant'),
]
