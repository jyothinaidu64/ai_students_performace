from ortools.sat.python import cp_model
from django.db import transaction

from timetable.models import TimetableEntry
from students.models import SchoolClass
from assessments.models import Subject
from accounts.models import User


# Days and periods used across the app
DAYS = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
]

PERIODS = [1, 2, 3, 4, 5, 6]  # 6 periods per day


def _compute_sessions_per_subject(subjects, total_slots):
    """
    Simple helper to decide how many sessions per week each subject should get.

    Strategy:
      - Distribute slots as evenly as possible across subjects.
      - If there is a remainder, assign +1 extra session to the first few subjects.
    """
    num_subjects = len(subjects)
    base = total_slots // num_subjects
    remainder = total_slots % num_subjects

    sessions = {}
    for idx, subj in enumerate(subjects):
        sessions[subj.id] = base + (1 if idx < remainder else 0)
    return sessions


def generate_timetable_for_class(school_class: SchoolClass):
    """
    Generate a weekly timetable for a single SchoolClass using OR-Tools CP-SAT.

    - Uses DAYS (Mon–Fri) and PERIODS (e.g. 1..6).
    - Assigns exactly one subject to each (day, period).
    - Balances total sessions per subject across the week.
    - Assigns teachers in a simple round-robin manner.

    This function DOES NOT handle cross-class teacher conflicts.
    That would require a global multi-class solve.
    """
    # Fetch all subjects
    subjects = list(Subject.objects.order_by("name"))
    if not subjects:
        raise ValueError("No Subject records found. Seed subjects before generating timetable.")

    # Fetch all teacher users
    teachers = list(User.objects.filter(role=User.Role.TEACHER).order_by("username"))
    if not teachers:
        raise ValueError("No teachers with role=TEACHER found. Seed teachers before generating timetable.")

    num_days = len(DAYS)
    num_periods = len(PERIODS)
    total_slots = num_days * num_periods

    # Decide how many sessions per week each subject should get
    sessions_per_subject = _compute_sessions_per_subject(subjects, total_slots)

    model = cp_model.CpModel()

    # Map subjects to indices
    subject_ids = [s.id for s in subjects]
    subject_index_by_id = {s.id: idx for idx, s in enumerate(subjects)}
    num_subjects = len(subjects)

    # x[(d, p, s_idx)] = 1 if subject s_idx is scheduled at day d, period p
    x = {}
    for d_idx in range(num_days):
        for p_idx in range(num_periods):
            for s_idx in range(num_subjects):
                x[(d_idx, p_idx, s_idx)] = model.NewBoolVar(
                    f"x_d{d_idx}_p{p_idx}_s{s_idx}"
                )

    # 1) Each slot (day, period) must have exactly ONE subject
    for d_idx in range(num_days):
        for p_idx in range(num_periods):
            model.Add(
                sum(x[(d_idx, p_idx, s_idx)] for s_idx in range(num_subjects)) == 1
            )

    # 2) Each subject must appear a fixed number of times in the week
    for s_idx, subj in enumerate(subjects):
        required_sessions = sessions_per_subject[subj.id]
        model.Add(
            sum(
                x[(d_idx, p_idx, s_idx)]
                for d_idx in range(num_days)
                for p_idx in range(num_periods)
            ) == required_sessions
        )

    # Optional: Mild objective just to make solver "happy" (not really necessary)
    model.Maximize(0)

    # Solve
    solver = cp_model.CpSolver()
    solver_status = solver.Solve(model)

    if solver_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("No feasible timetable found by OR-Tools for this class.")

    # Build solution: for each (day, period) pick the subject with x=1
    # Then assign teachers in round-robin
    with transaction.atomic():
        # Existing entries for this class should already be deleted by caller,
        # but you can uncomment the next line if you want to be extra safe:
        # TimetableEntry.objects.filter(school_class=school_class).delete()

        teacher_count = len(teachers)
        teacher_counter = 0

        for d_idx, (day_code, _day_label) in enumerate(DAYS):
            for p_idx, period in enumerate(PERIODS):
                chosen_subject = None
                for s_idx, subj in enumerate(subjects):
                    if solver.Value(x[(d_idx, p_idx, s_idx)]) == 1:
                        chosen_subject = subj
                        break

                if chosen_subject is None:
                    # Should not happen due to constraints
                    continue

                # Pick teacher in round-robin fashion
                teacher = teachers[teacher_counter % teacher_count]
                teacher_counter += 1

                TimetableEntry.objects.create(
                    school_class=school_class,
                    day_of_week=day_code,
                    period=period,
                    subject=chosen_subject,
                    teacher=teacher,
                )
