from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from .models import EMPLOYEE_ROLES, ADMIN_ROLES, ALL_STAFF_ROLES


def role_required(allowed_groups):
    """
    Decorator to check role groups.
    allowed_groups: list of role strings or group names:
      'user'        -> any authenticated user
      'employee'    -> any employee role (trainee/staff) or staff-rank
      'admin'       -> full admin roles only (ADMIN_ROLES)
      'staff'       -> all staff-rank roles (ADMIN_ROLES + flight_host)
      <role_string> -> exact role match
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            role = request.user.profile.role

            allowed = False
            for group in allowed_groups:
                if group == 'admin' and role in ADMIN_ROLES:
                    allowed = True
                elif group == 'staff' and role in ALL_STAFF_ROLES:
                    allowed = True
                elif group == 'employee' and (role in EMPLOYEE_ROLES or role in ALL_STAFF_ROLES):
                    allowed = True
                elif group == 'user':
                    allowed = True
                elif group == role:
                    allowed = True
            if not allowed:
                messages.error(request, '你没有权限访问此页面')
                return redirect('home')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
