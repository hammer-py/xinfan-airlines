from django.urls import path
from . import views

urlpatterns = [
    path('', views.flight_list_view, name='flight_list'),
    path('create/', views.flight_create_view, name='flight_create'),
    path('<int:pk>/', views.flight_detail_view, name='flight_detail'),
    path('<int:pk>/edit/', views.flight_edit_view, name='flight_edit'),
    path('<int:pk>/delete/', views.flight_delete_view, name='flight_delete'),
    path('<int:pk>/signup/', views.flight_signup_view, name='flight_signup'),
    path('my-signups/', views.my_signups_view, name='my_signups'),
    path('admin-signups/', views.admin_signups_view, name='admin_signups'),
]
