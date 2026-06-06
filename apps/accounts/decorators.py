from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import EMPLOYEE_ROLES

def role_required(allowed_groups):
    """
    Decorator to check role groups.
    allowed_groups: list of role strings or group names:
      'user'     -> any non-employee, non-admin role
      'employee' -> any employee role (trainee or staff) or admin
      'staff'    -> any official employee role or admin
      'admin'    -> admin only
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            role = request.user.profile.role

            allowed = False
            for group in allowed_groups:
                if group == 'admin' and role == 'admin':
                    allowed = True
                elif group == 'employee' and (role in EMPLOYEE_ROLES or role == 'admin'):
                    allowed = True
                elif group == 'user':
                    allowed = True  # any authenticated user
                elif group == role:
                    allowed = True  # exact role match
            if not allowed:
                messages.error(request, '你没有权限访问此页面')
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
