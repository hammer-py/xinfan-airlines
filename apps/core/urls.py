from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('vip-club/', views.vip_club_view, name='vip_club'),
    path('hkhos-demo/', views.hkhos_demo_view, name='hkhos_demo'),
]
