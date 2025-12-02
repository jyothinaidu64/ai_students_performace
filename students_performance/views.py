# students_performance/views.py

from django.shortcuts import render


def permission_denied_view(request, exception=None):
    """
    Render a friendly 403 page when PermissionDenied is raised.
    """
    return render(request, "403.html", status=403)
