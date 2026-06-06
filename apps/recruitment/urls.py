from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list_view, name='job_list'),
    path('<int:pk>/', views.job_detail_view, name='job_detail'),
    path('<int:pk>/apply/', views.job_apply_view, name='job_apply'),
    path('my/', views.my_applications_view, name='my_applications'),
    path('admin/manage/', views.admin_recruitment_view, name='admin_recruitment'),
    path('admin/applications/', views.admin_applications_view, name='admin_applications'),
]
