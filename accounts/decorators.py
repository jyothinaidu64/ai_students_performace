# accounts/decorators.py

from functools import wraps

from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied


def role_required(*allowed_roles):
    """
    Usage:
        @role_required("STUDENT")
        @role_required("MANAGEMENT", "CLASS_TEACHER")

    Compares against request.user.role.

    You can choose behavior on wrong role:
    - For strict 403: raise PermissionDenied
    - For softer UX: redirect to 'dashboard'
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user

            if not user.is_authenticated:
                return redirect("login")

            if user.role not in allowed_roles:
                # Option A: strict
                # raise PermissionDenied

                # Option B: soft redirect (recommended for UX)
                return redirect("dashboard")

            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator
