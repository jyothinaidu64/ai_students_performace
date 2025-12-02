# communication/views.py

import datetime

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from accounts.decorators import role_required
from students.models import Student
from .models import Announcement, Event, LeaveRequest, ParentConcern
from .forms import (
    ParentConcernForm,
    AnnouncementForm,
    LeaveRequestForm,
    EventForm,
)


# -------------------------------------------------------------------
# Helper role checks
# -------------------------------------------------------------------

def is_teacher_or_admin(user):
    """
    Teachers + management (for reviewing leave, creating announcements, etc.).
    """
    return user.is_authenticated and user.role in [
        user.Role.MANAGEMENT,
        user.Role.CLASS_TEACHER,
        user.Role.TEACHER,
    ]


def is_class_teacher(user):
    """
    Strictly class teachers (for class-level leave review).
    """
    return user.is_authenticated and user.role == user.Role.CLASS_TEACHER


# -------------------------------------------------------------------
# Announcements
# -------------------------------------------------------------------

@login_required
def my_announcements_view(request):
    """
    Simple announcements list for any logged-in user.
    Later you can filter by school/class/role.
    """
    anns = Announcement.objects.order_by("-created_at")[:50]
    return render(
        request,
        "communication/my_announcements.html",
        {
            "announcements": anns,
            "nav_announcements_active": "active",
        },
    )


@user_passes_test(is_teacher_or_admin)
def announcement_create(request):
    """
    Create a new announcement (teachers / management only).
    """
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.created_by = request.user
            ann.save()
            return redirect("communication:my_announcements")
    else:
        form = AnnouncementForm()

    return render(
        request,
        "communication/announcement_form.html",
        {
            "form": form,
            "is_edit": False,
            "nav_announcements_active": "active",
        },
    )


# -------------------------------------------------------------------
# Events / Calendar
# -------------------------------------------------------------------

@login_required
def event_calendar_view(request):
    """
    Public calendar view of upcoming events & holidays.
    """
    today = datetime.date.today()
    events = Event.objects.filter(date__gte=today).order_by("date", "start_time")
    return render(
        request,
        "communication/calendar.html",
        {
            "events": events,
            "nav_calendar_active": "active",
        },
    )


@user_passes_test(is_teacher_or_admin)
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            e = form.save(commit=False)
            e.created_by = request.user
            e.save()
            return redirect("communication:calendar_admin")
    else:
        form = EventForm()

    return render(request, "communication/event_form.html", {"form": form, "is_edit": False})



# -------------------------------------------------------------------
# Leave Management – student side
# -------------------------------------------------------------------

@role_required("STUDENT")
def create_leave_request(request):
    """
    Student applies for leave.
    Renders the nice leave_form.html.
    """
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        # Misconfigured account: student role but no Student profile
        return render(
            request,
            "communication/no_student_profile.html",
            {"user": request.user},
            status=404,
        )

    if request.method == "POST":
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.student = student
            leave.save()
            return redirect("communication:my_leaves")
    else:
        form = LeaveRequestForm()

    return render(
        request,
        "communication/leave_form.html",
        {
            "form": form,
            "nav_leave_new_active": "active",
        },
    )


@role_required("STUDENT")
def my_leave_requests(request):
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return render(
            request,
            "communication/no_student_profile.html",
            {"user": request.user},
            status=404,
        )

    leaves = LeaveRequest.objects.filter(student=student).order_by("-submitted_at")
    return render(
        request,
        "communication/my_leave_requests.html",
        {
            "leave_requests": leaves,
            "nav_leave_list_active": "active",
        },
    )



# -------------------------------------------------------------------
# Leave Management – teacher/admin side
# -------------------------------------------------------------------

@user_passes_test(is_class_teacher)
def class_leave_requests(request, class_section):
    """
    Class teacher view of leave requests for their class.
    NOTE: adjust filtering logic to how you model classes.
    """
    students = Student.objects.filter(class_section=class_section)
    leaves = LeaveRequest.objects.filter(student__in=students).order_by("-submitted_at")
    return render(
        request,
        "communication/class_leave_requests.html",
        {
            "leaves": leaves,
            "class_section": class_section,
            "nav_leave_class_active": "active",
        },
    )


@user_passes_test(is_teacher_or_admin)
def review_leave_request(request, pk):
    """
    Approve / reject a leave request.
    Expects POST with ?action=approve or ?action=reject.
    """
    leave = get_object_or_404(LeaveRequest, pk=pk)
    action = request.POST.get("action")  # "approve" or "reject"

    if action == "approve":
        leave.status = "APPROVED"
    elif action == "reject":
        leave.status = "REJECTED"

    leave.reviewed_by = request.user
    leave.reviewed_at = timezone.now()
    leave.save()

    # Redirect back to that class' leave list (or wherever you prefer)
    return redirect("communication:class_leave_requests", class_section=leave.student.class_section)


# -------------------------------------------------------------------
# Parent / Student Concerns
# -------------------------------------------------------------------

@role_required("STUDENT")
def create_concern(request):
    """
    Student/parent raises a concern.
    Uses concern_form.html.
    """
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return render(
            request,
            "communication/no_student_profile.html",
            {"user": request.user},
            status=404,
        )

    if request.method == "POST":
        form = ParentConcernForm(request.POST)
        if form.is_valid():
            concern = form.save(commit=False)
            concern.student = student
            concern.save()
            return redirect("communication:my_concerns")
    else:
        form = ParentConcernForm()

    return render(
        request,
        "communication/concern_form.html",
        {
            "form": form,
            "nav_concern_new_active": "active",
        },
    )


@role_required("STUDENT")
def my_concerns(request):
    """
    List of concerns created by the logged-in student/parent.
    Uses my_concerns.html.
    """
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return render(
            request,
            "communication/no_student_profile.html",
            {"user": request.user},
            status=404,
        )

    concerns = ParentConcern.objects.filter(student=student).order_by("-created_at")
    return render(
        request,
        "communication/my_concerns.html",
        {
            "concerns": concerns,
            "nav_concern_list_active": "active",
        },
    )


from django.db.models import Q

@role_required("MANAGEMENT", "CLASS_TEACHER")
def all_concerns(request):
    status_filter = request.GET.get("status", "all").upper()

    qs = ParentConcern.objects.select_related(
        "student__user",
        "student__school_class",
        "handled_by",
    ).order_by("-created_at")

    if status_filter in ["OPEN", "IN_PROGRESS", "RESOLVED"]:
        qs = qs.filter(status=status_filter)

    concerns = qs

    return render(
        request,
        "communication/all_concerns.html",
        {
            "concerns": concerns,
            "status_filter": status_filter.lower(),
            "nav_concerns_admin_active": "active",
        },
    )



from django.db.models import Q

def is_class_teacher(user):
    return user.is_authenticated and user.role == user.Role.CLASS_TEACHER


@user_passes_test(is_class_teacher)
def class_leave_requests(request, class_section):
    """
    Class teacher view of leave requests for their class.
    Adds simple status filter via ?status=pending/approved/rejected/all
    """

    status_filter = request.GET.get("status", "all").upper()  # "PENDING", "APPROVED", "REJECTED", "ALL"

    # Adjust this filter if your Student model stores class differently
    students = Student.objects.filter(school_class__section=class_section) | Student.objects.filter(
        school_class__name=class_section
    )

    leaves_qs = LeaveRequest.objects.filter(student__in=students)

    if status_filter in ["PENDING", "APPROVED", "REJECTED"]:
        leaves_qs = leaves_qs.filter(status=status_filter)

    leaves = leaves_qs.select_related("student__user").order_by("-submitted_at")

    return render(
        request,
        "communication/class_leave_requests.html",
        {
            "leaves": leaves,
            "class_section": class_section,
            "status_filter": status_filter.lower(),
            "nav_leave_class_active": "active",
        },
    )

from django.contrib.auth.decorators import user_passes_test

def is_teacher_or_admin(user):
    return user.is_authenticated and user.role in [
        user.Role.MANAGEMENT,
        user.Role.CLASS_TEACHER,
        user.Role.TEACHER,
    ]


@user_passes_test(is_teacher_or_admin)
def admin_announcements_view(request):
    """
    Management/teacher view: list of all announcements.
    You can later add filters (by school, audience, etc.).
    """
    anns = Announcement.objects.select_related("created_by").order_by("-created_at")[:100]
    return render(
        request,
        "communication/admin_announcements.html",
        {
            "announcements": anns,
            "nav_announcements_active": "active",
        },
    )

@user_passes_test(is_teacher_or_admin)
def event_calendar_admin(request):
    """
    Management/teacher view of all upcoming events.
    """
    today = datetime.date.today()
    events = (
        Event.objects
        .select_related("created_by")
        .filter(date__gte=today)
        .order_by("date", "start_time")
    )

    return render(
        request,
        "communication/calendar_admin.html",
        {
            "events": events,
            "nav_calendar_active": "active",
        },
    )
