# students_performance/urls.py

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler403

from accounts.views import dashboard_router, RoleBasedLoginView
from django.contrib.auth.views import LogoutView


def home(request):
    """
    Home page.
    If user is authenticated, send them to the right dashboard.
    Otherwise show landing content.
    """
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html")


urlpatterns = [
    path("", home, name="home"),

    path("dashboard/", dashboard_router, name="dashboard"),
    path("admin/", admin.site.urls),

    # Custom login/logout
    path("accounts/login/", RoleBasedLoginView.as_view(), name="login"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),

    # Other auth URLs (password reset, change, etc.)
    path("accounts/", include("django.contrib.auth.urls")),

    path("analytics/", include("analytics.urls")),
    path("students/", include("students.urls")),
    path("assessments/", include("assessments.urls")),
    path("timetable/", include("timetable.urls")),
    path("finance/", include("finance.urls")),
    path("communication/", include("communication.urls")),
    
    # API endpoints
    path("api/", include("students_performance.api_router")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom 403 handler
handler403 = "students_performance.views.permission_denied_view"
