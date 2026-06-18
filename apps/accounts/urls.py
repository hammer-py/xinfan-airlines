from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    path('admin-panel/users/', views.admin_users_view, name='admin_users'),
    path('captcha-refresh/', views.captcha_refresh, name='captcha_refresh'),
]
