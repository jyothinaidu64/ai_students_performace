from django.shortcuts import render, redirect
from accounts.decorators import role_required
from .models import TimetableEntry
from students.models import SchoolClass
from django.shortcuts import render, get_object_or_404
from accounts.decorators import role_required
from students.models import SchoolClass
from .models import TimetableEntry
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from accounts.models import User
DAYS = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
]

PERIODS = [1, 2, 3, 4, 5, 6]  # adjust if you have more/less


@role_required("MANAGEMENT")
def generate_timetable_view(request):
    if request.method == "POST":
        ok = generate_timetable()
        # use messages for success/failure
        return redirect("timetable_overview")
    return render(request, "timetable/generate.html")

@role_required("MANAGEMENT", "CLASS_TEACHER", "STUDENT")
def class_timetable_view(request, class_id):
    school_class = SchoolClass.objects.get(id=class_id)
    entries = TimetableEntry.objects.filter(school_class=school_class)
    # Build grid days x periods
    grid = [[None for _ in range(PERIODS)] for _ in range(DAYS)]
    for e in entries:
        grid[e.day_of_week][e.period] = e
    return render(request, "timetable/class_timetable.html", {"school_class": school_class, "grid": grid})
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("OK")






@role_required("MANAGEMENT")
def timetable_class_list(request):
    """
    Management view: list all classes with 'View timetable' links.
    """
    classes = SchoolClass.objects.order_by("name", "section")
    return render(request, "timetable/class_list.html", {
        "classes": classes,
    })


@role_required("MANAGEMENT")
def timetable_class_view(request, class_id):
    """
    Show the timetable grid for a single class.
    """
    school_class = get_object_or_404(SchoolClass, id=class_id)

    # Fetch all entries for this class
    entries = TimetableEntry.objects.filter(school_class=school_class).select_related("subject", "teacher")

    # Build grid: day -> period -> entry
    grid = {day_code: {p: None for p in PERIODS} for (day_code, _) in DAYS}

    for e in entries:
        if e.day_of_week in grid and e.period in grid[e.day_of_week]:
            grid[e.day_of_week][e.period] = e

    context = {
        "school_class": school_class,
        "days": DAYS,
        "periods": PERIODS,
        "grid": grid,
    }
    return render(request, "timetable/class_timetable.html", context)

from django.contrib import messages
from django.shortcuts import redirect
from .models import TimetableEntry
from .solver import generate_timetable_for_class  # adapt import to your actual module


@role_required("MANAGEMENT")
def timetable_regenerate_for_class(request, class_id):
    """
    Re-generate timetable for a single class using OR-Tools.
    """
    school_class = get_object_or_404(SchoolClass, id=class_id)

    # Safety: only allow POST
    if request.method != "POST":
        messages.error(request, "Timetable can only be regenerated via POST.")
        return redirect("timetable_class_view", class_id=school_class.id)

    # Delete existing entries for this class
    TimetableEntry.objects.filter(school_class=school_class).delete()

    # Call your OR-Tools-based generator
    generate_timetable_for_class(school_class)

    messages.success(request, f"Timetable regenerated for {school_class}.")
    return redirect("timetable_class_view", class_id=school_class.id)



@login_required
def teacher_timetable_view(request):
    """
    Timetable for the logged-in teacher or class teacher across all classes.
    Shows any TimetableEntry rows where this user is the teacher.
    """
    user = request.user
    if user.role not in (User.Role.TEACHER, User.Role.CLASS_TEACHER):
        return HttpResponseForbidden("You do not have access to the teacher timetable.")

    entries = TimetableEntry.objects.filter(teacher=user).select_related("school_class", "subject")

    days = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
    ]
    periods = [1, 2, 3, 4, 5, 6]

    # Build grid: day -> period -> list of entries
    grid = {d[0]: {p: [] for p in periods} for d in days}

    for e in entries:
        grid[e.day_of_week][e.period].append(e)

    context = {
        "teacher": user,
        "days": days,
        "periods": periods,
        "grid": grid,
    }
    return render(request, "timetable/teacher_timetable.html", context)

