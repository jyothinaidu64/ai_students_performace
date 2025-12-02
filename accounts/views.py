# accounts/views.py

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView

from accounts.decorators import role_required


def dashboard_router(request):
    """
    Central router that sends the user to the correct dashboard
    based on their role.
    """
    user = request.user

    if not user.is_authenticated:
        return redirect("login")

    # Adjust these role names and URLs based on your project
    if user.role == user.Role.MANAGEMENT:
        return redirect("management_dashboard")
    elif user.role == user.Role.CLASS_TEACHER:
        return redirect("class_teacher_dashboard")
    elif user.role == user.Role.TEACHER:
        return redirect("teacher_timetable_view")
    elif user.role == user.Role.STUDENT:
        return redirect("student_dashboard")

    # Fallback
    return redirect("home")


class RoleBasedLoginView(LoginView):
    """
    Custom login that:
    - Supports "remember me"
    - Redirects to ?next=... if provided
    - Otherwise goes to the role-based dashboard router
    """
    template_name = "registration/login.html"

    def form_valid(self, form):
        # Handle "remember me"
        remember_me = self.request.POST.get("remember_me")
        if remember_me:
            # 30 days
            self.request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            # Session ends when browser closes
            self.request.session.set_expiry(0)

        # Perform the default login
        response = super().form_valid(form)

        # Respect next= param if present
        next_url = self.request.POST.get("next") or self.request.GET.get("next")
        if next_url:
            return redirect(next_url)

        # Default redirect: dashboard router
        return redirect("dashboard")
