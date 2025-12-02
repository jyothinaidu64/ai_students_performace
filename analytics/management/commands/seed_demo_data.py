# analytics/management/commands/seed_demo_data.py

import math
import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import transaction

from schools.models import School
from students.models import SchoolClass, Student
from assessments.models import Subject, Assessment
from timetable.models import TimetableEntry

# Optional models (if you have them)
try:
    from analytics.models import StudentRisk, NextExamPrediction
except Exception:
    StudentRisk = None
    NextExamPrediction = None

# Finance models (optional)
try:
    from finance.models import FeeStructure, FeeAssignment, FeePayment
except Exception:
    FeeStructure = None
    FeeAssignment = None
    FeePayment = None

# Communication models (optional)
try:
    from communication.models import Announcement, Event, LeaveRequest, ParentConcern
except Exception:
    Announcement = None
    Event = None
    LeaveRequest = None
    ParentConcern = None


User = get_user_model()


class Command(BaseCommand):
    help = "Wipe existing demo data and seed fresh end-to-end test data (~1000 students, finance, communication)."

    # ------------------------------------------------------------------
    # CONFIG (tweak here if you want different sizes)
    # ------------------------------------------------------------------
    TOTAL_STUDENTS = 1000
    GV_SHARE = 0.5          # 50% of students in Green Valley
    SR_SHARE = 0.5          # 50% of students in Sunrise

    # For each grade, how many sections? (realistic multi-section school)
    CLASS_NAMES = ["LKG", "UKG"] + [f"{i}" for i in range(1, 11)]
    SECTIONS = ["A", "B", "C", "D"]   # 4 sections per grade

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("WIPING existing demo data..."))

        # ------------------------------------------------------------------
        # DELETE existing data, order matters because of FK constraints
        # ------------------------------------------------------------------
        TimetableEntry.objects.all().delete()
        Assessment.objects.all().delete()

        if NextExamPrediction:
            NextExamPrediction.objects.all().delete()
        if StudentRisk:
            StudentRisk.objects.all().delete()

        # Finance
        if FeePayment:
            FeePayment.objects.all().delete()
        if FeeAssignment:
            FeeAssignment.objects.all().delete()
        if FeeStructure:
            FeeStructure.objects.all().delete()

        # Communication
        if LeaveRequest:
            LeaveRequest.objects.all().delete()
        if ParentConcern:
            ParentConcern.objects.all().delete()
        if Event:
            Event.objects.all().delete()
        if Announcement:
            Announcement.objects.all().delete()

        Student.objects.all().delete()
        SchoolClass.objects.all().delete()
        Subject.objects.all().delete()
        School.objects.all().delete()

        # Wipe non-superuser accounts (keep superusers so you don't lock yourself out)
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS("All old demo data removed."))

        # ---------------------------------------------------------------------
        # 1. Create Schools
        # ---------------------------------------------------------------------
        self.stdout.write("Creating schools...")

        gv_school = School.objects.create(
            name="Green Valley Public School",
            short_name="Green Valley",
            slug="green-valley",
            tagline="Excellence through Analytics",
            is_active=True,
        )

        sr_school = School.objects.create(
            name="Sunrise International School",
            short_name="Sunrise",
            slug="sunrise-international",
            tagline="Learning with Light",
            is_active=True,
        )

        # ---------------------------------------------------------------------
        # 2. Create Subjects (shared for simplicity)
        # ---------------------------------------------------------------------
        self.stdout.write("Creating subjects...")

        math = Subject.objects.create(name="Mathematics")
        sci = Subject.objects.create(name="Science")
        eng = Subject.objects.create(name="English")

        subjects = [math, sci, eng]

        # ---------------------------------------------------------------------
        # 3. Create Users (Management, Teachers)
        # ---------------------------------------------------------------------
        self.stdout.write("Creating management & core staff users...")

        # Management users (Principals)
        gv_admin = User.objects.create_user(
            username="gv_admin",
            email="gv_admin@example.com",
            password="Password123",
            role=User.Role.MANAGEMENT,
            school=gv_school,
            first_name="Ramesh",
            last_name="Prasad",
        )

        sr_admin = User.objects.create_user(
            username="sr_admin",
            email="sr_admin@example.com",
            password="Password123",
            role=User.Role.MANAGEMENT,
            school=sr_school,
            first_name="Shalini",
            last_name="Menon",
        )

        # A few extra management/support staff (for realism)
        User.objects.create_user(
            username="gv_vice_principal",
            email="gv_vice_principal@example.com",
            password="Password123",
            role=User.Role.MANAGEMENT,
            school=gv_school,
            first_name="Anjali",
            last_name="Sharma",
        )
        User.objects.create_user(
            username="sr_vice_principal",
            email="sr_vice_principal@example.com",
            password="Password123",
            role=User.Role.MANAGEMENT,
            school=sr_school,
            first_name="Rohit",
            last_name="Verma",
        )

        # ---------------------------------------------------------------------
        # 4. Create Classes (LKG–10 with sections A–D) for each school
        # ---------------------------------------------------------------------
        self.stdout.write("Creating classes (multi-section)...")

        gv_classes = {}  # (grade, section) -> SchoolClass
        sr_classes = {}

        for name in self.CLASS_NAMES:
            for section in self.SECTIONS:
                gv_classes[(name, section)] = SchoolClass.objects.create(
                    school=gv_school,
                    name=name,
                    section=section,
                )
                sr_classes[(name, section)] = SchoolClass.objects.create(
                    school=sr_school,
                    name=name,
                    section=section,
                )

        # ---------------------------------------------------------------------
        # 5. Create Teachers (Class teachers + subject teachers)
        # ---------------------------------------------------------------------
        self.stdout.write("Creating teachers...")

        first_names = [
            "Ravi", "Sita", "Arjun", "Priya", "Kiran", "Lakshmi",
            "Vikram", "Neha", "Sanjay", "Pooja", "Harsh", "Anita"
        ]
        last_names = [
            "Sharma", "Reddy", "Iyer", "Patel", "Nair",
            "Gupta", "Kumar", "Rao", "Desai", "Mukherjee"
        ]

        def create_class_teachers_for_school(school, classes_dict, prefix):
            """
            Create one CLASS_TEACHER per SchoolClass and assign as class_teacher.
            """
            class_teacher_users = {}
            for (grade, section), school_class in classes_dict.items():
                username = f"{prefix}_ct_{grade}{section}"
                fn = random.choice(first_names)
                ln = random.choice(last_names)
                ct_user = User.objects.create_user(
                    username=username.lower().replace(" ", ""),
                    email=f"{username.lower()}@example.com",
                    password="Password123",
                    role=User.Role.CLASS_TEACHER,
                    school=school,
                    first_name=fn,
                    last_name=ln,
                )
                # Assign to SchoolClass if field exists
                if hasattr(school_class, "class_teacher"):
                    school_class.class_teacher = ct_user
                    school_class.save()
                class_teacher_users[(grade, section)] = ct_user
            return class_teacher_users

        gv_class_teachers = create_class_teachers_for_school(gv_school, gv_classes, "gv")
        sr_class_teachers = create_class_teachers_for_school(sr_school, sr_classes, "sr")

        # Subject teachers per school (a few specialists)
        def create_subject_teachers(prefix, school):
            math_t = User.objects.create_user(
                username=f"{prefix}_t_math",
                email=f"{prefix}_t_math@example.com",
                password="Password123",
                role=User.Role.TEACHER,
                school=school,
                first_name="Meera",
                last_name="Patel",
            )
            sci_t = User.objects.create_user(
                username=f"{prefix}_t_science",
                email=f"{prefix}_t_science@example.com",
                password="Password123",
                role=User.Role.TEACHER,
                school=school,
                first_name="Rahul",
                last_name="Iyer",
            )
            eng_t = User.objects.create_user(
                username=f"{prefix}_t_english",
                email=f"{prefix}_t_english@example.com",
                password="Password123",
                role=User.Role.TEACHER,
                school=school,
                first_name="Divya",
                last_name="Rao",
            )
            return math_t, sci_t, eng_t

        gv_math_teacher, gv_sci_teacher, gv_eng_teacher = create_subject_teachers("gv", gv_school)
        sr_math_teacher, sr_sci_teacher, sr_eng_teacher = create_subject_teachers("sr", sr_school)

        # ---------------------------------------------------------------------
        # 6. Create Students (~1000 total, split between schools)
        # ---------------------------------------------------------------------
        self.stdout.write("Creating students (~1000)...")

        total_gv_students = int(self.TOTAL_STUDENTS * self.GV_SHARE)
        total_sr_students = self.TOTAL_STUDENTS - total_gv_students

        # slight bias: put more students in higher grades for realism
        def grade_weight(grade_name):
            if grade_name in ["LKG", "UKG"]:
                return 0.5
            else:
                g = int(grade_name)
                # older grades slightly more students
                return 0.5 + (g / 10.0)

        # Precompute grade weights
        grade_weights = {name: grade_weight(name) for name in self.CLASS_NAMES}

        def fill_students_for_school(school, classes_dict, prefix, target_count):
            students_by_class = {key: [] for key in classes_dict.keys()}
            all_students = []

            roll_counters = {key: 0 for key in classes_dict.keys()}

            # flatten classes by weight
            class_keys = list(classes_dict.keys())
            weighted_class_keys = []
            for grade, section in class_keys:
                w = grade_weights[grade]
                count = max(1, int(w * 10))
                weighted_class_keys.extend([(grade, section)] * count)

            # create students until we hit target_count
            for idx in range(1, target_count + 1):
                grade, section = random.choice(weighted_class_keys)
                school_class = classes_dict[(grade, section)]
                roll_counters[(grade, section)] += 1
                roll = roll_counters[(grade, section)]

                fn = random.choice(first_names)
                ln = random.choice(last_names)

                # build a readable username, e.g. gv_10A_001
                safe_grade = grade.replace(" ", "").upper()
                username = f"{prefix}{safe_grade}{section}_{roll:03d}".lower()

                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password="Password123",
                    role=User.Role.STUDENT,
                    school=school,
                    first_name=fn,
                    last_name=ln,
                )

                admission_number = f"{prefix.upper()}{safe_grade}{section}-{roll:04d}"

                student = Student.objects.create(
                    user=user,
                    school_class=school_class,
                    admission_number=admission_number,
                    roll_number=str(roll),
                )

                students_by_class[(grade, section)].append(student)
                all_students.append(student)

            return all_students, students_by_class

        gv_students, gv_students_by_class = fill_students_for_school(
            gv_school, gv_classes, "gv_", total_gv_students
        )
        sr_students, sr_students_by_class = fill_students_for_school(
            sr_school, sr_classes, "sr_", total_sr_students
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(gv_students)} students in Green Valley and "
                f"{len(sr_students)} students in Sunrise."
            )
        )

        # ---------------------------------------------------------------------
        # 7. Create Assessments for students (for ML & dashboards)
        # ---------------------------------------------------------------------
        self.stdout.write("Creating assessments for ML & dashboard testing...")

        base_date = date(2025, 4, 1)

        def add_assessment(student, subject, exam_name, offset_days, marks, max_marks=100, att=90, assignments=8):
            Assessment.objects.create(
                student=student,
                subject=subject,
                exam_name=exam_name,
                exam_date=base_date + timedelta(days=offset_days),
                term="Term 1",
                marks_obtained=marks,
                max_marks=max_marks,
                attendance_percent=att,
                assignments_completed=assignments,
            )

        # -- Focus class: GV 10A --
        gv_10A_class = gv_classes[("10", "A")]
        gv_10A_students = gv_students_by_class[("10", "A")]

        if len(gv_10A_students) >= 3:
            stu_weak = gv_10A_students[0]  # high risk profile
            stu_medium = gv_10A_students[1]  # medium
            stu_strong = gv_10A_students[2]  # low risk

            # Weak student: low & unstable scores
            math_series_weak = [(0, 30), (30, 35), (60, 28), (90, 32)]
            for i, (offset, marks) in enumerate(math_series_weak, start=1):
                add_assessment(stu_weak, math, f"Math UT{i}", offset, marks, att=75, assignments=4)

            sci_series_weak = [(5, 40), (35, 42), (65, 38), (95, 39)]
            for i, (offset, marks) in enumerate(sci_series_weak, start=1):
                add_assessment(stu_weak, sci, f"Sci UT{i}", offset, marks, att=78, assignments=5)

            eng_series_weak = [(10, 45), (40, 48), (70, 44), (100, 46)]
            for i, (offset, marks) in enumerate(eng_series_weak, start=1):
                add_assessment(stu_weak, eng, f"Eng UT{i}", offset, marks, att=80, assignments=6)

            # Medium student: mid scores with slight improvement
            math_series_med = [(0, 55), (30, 58), (60, 60), (90, 62)]
            for i, (offset, marks) in enumerate(math_series_med, start=1):
                add_assessment(stu_medium, math, f"Math UT{i}", offset, marks, att=88, assignments=7)

            sci_series_med = [(5, 60), (35, 62), (65, 64), (95, 66)]
            for i, (offset, marks) in enumerate(sci_series_med, start=1):
                add_assessment(stu_medium, sci, f"Sci UT{i}", offset, marks, att=90, assignments=8)

            eng_series_med = [(10, 65), (40, 68), (70, 70), (100, 72)]
            for i, (offset, marks) in enumerate(eng_series_med, start=1):
                add_assessment(stu_medium, eng, f"Eng UT{i}", offset, marks, att=92, assignments=9)

            # Strong student: high and improving scores
            math_series_strong = [(0, 80), (30, 82), (60, 85), (90, 88)]
            for i, (offset, marks) in enumerate(math_series_strong, start=1):
                add_assessment(stu_strong, math, f"Math UT{i}", offset, marks, att=95, assignments=10)

            sci_series_strong = [(5, 78), (35, 80), (65, 83), (95, 86)]
            for i, (offset, marks) in enumerate(sci_series_strong, start=1):
                add_assessment(stu_strong, sci, f"Sci UT{i}", offset, marks, att=96, assignments=10)

            eng_series_strong = [(10, 82), (40, 85), (70, 88), (100, 90)]
            for i, (offset, marks) in enumerate(eng_series_strong, start=1):
                add_assessment(stu_strong, eng, f"Eng UT{i}", offset, marks, att=97, assignments=10)

        # --- Generate simple random assessments for ALL GV 10A students ---
        self.stdout.write("Adding simple assessment history for all GV 10A students...")

        for stu in gv_10A_students:
            # Skip the 3 special ones above (they already have richer data)
            if stu in [stu_weak, stu_medium, stu_strong]:
                continue

            # Give each student 3 tests per subject with reasonable scores
            for subj in [math, sci, eng]:
                base_score = random.randint(40, 85)
                for i, offset in enumerate([0, 40, 80], start=1):
                    jitter = random.randint(-10, 10)
                    marks = max(0, min(100, base_score + jitter))
                    add_assessment(
                        stu,
                        subj,
                        f"{subj.name} UT{i}",
                        offset,
                        marks,
                        att=random.randint(80, 98),
                        assignments=random.randint(6, 10),
                    )

        # --- Optionally: give some Sunrise students data too ---
        self.stdout.write("Adding basic assessment history for some Sunrise 10A students...")

        sr_10A_students = sr_students_by_class.get(("10", "A"), [])
        for stu in sr_10A_students[:15]:  # only first 15 for demo
            for subj in [math, sci, eng]:
                base_score = random.randint(45, 90)
                for i, offset in enumerate([0, 35, 70], start=1):
                    jitter = random.randint(-8, 8)
                    marks = max(0, min(100, base_score + jitter))
                    add_assessment(
                        stu,
                        subj,
                        f"{subj.name} UT{i}",
                        offset,
                        marks,
                        att=random.randint(82, 99),
                        assignments=random.randint(7, 10),
                    )

        # ---------------------------------------------------------------------
        # 8. Create simple timetables for GV 10A
        # ---------------------------------------------------------------------
        self.stdout.write("Creating sample timetables for GV 10A...")

        DAY_MAP = {
            "MON": 1,
            "TUE": 2,
            "WED": 3,
            "THU": 4,
            "FRI": 5,
        }

        days = ["MON", "TUE", "WED", "THU", "FRI"]
        periods = [1, 2, 3, 4, 5, 6]

        subject_cycle = [math, eng, sci, math, eng, sci]
        teacher_map = {
            math.id: gv_math_teacher,
            sci.id: gv_sci_teacher,
            eng.id: gv_eng_teacher,
        }

        for d in days:
            for idx, p in enumerate(periods):
                subject = subject_cycle[idx]
                teacher = teacher_map[subject.id]
                TimetableEntry.objects.create(
                    school_class=gv_10A_class,
                    day_of_week=DAY_MAP[d],
                    period=p,
                    subject=subject,
                    teacher=teacher,
                )

        # ---------------------------------------------------------------------
        # 9. Finance: Fee Structures, Assignments, Payments
        # ---------------------------------------------------------------------
        if FeeStructure and FeeAssignment and FeePayment:
            self.stdout.write("Creating finance data (fees, assignments, payments)...")

            def create_fee_structures_for_school(school, prefix):
                annual = FeeStructure.objects.create(
                    name="Annual Tuition Fee 2025",
                    class_section="All",
                    amount=30000,
                )
                transport = FeeStructure.objects.create(
                    name="Bus Transport Fee 2025",
                    class_section="All",
                    amount=5000,
                )
                return annual, transport

            gv_annual, gv_transport = create_fee_structures_for_school(gv_school, "gv")
            sr_annual, sr_transport = create_fee_structures_for_school(sr_school, "sr")

            # Assign fees to all students
            def assign_fees_to_students(students, annual_fs, transport_fs, prefix):
                assignments = []
                for idx, stu in enumerate(students, start=1):
                    # annual fee assignment
                    fa_annual = FeeAssignment.objects.create(
                        student=stu,
                        fee_structure=annual_fs,
                        total_amount=annual_fs.amount,
                        discount_amount=0,
                    )
                    assignments.append(fa_annual)

                    # give transport fee to ~60% of students
                    if random.random() < 0.6:
                        fa_trans = FeeAssignment.objects.create(
                            student=stu,
                            fee_structure=transport_fs,
                            total_amount=transport_fs.amount,
                            discount_amount=0,
                        )
                        assignments.append(fa_trans)

                return assignments

            gv_fee_assignments = assign_fees_to_students(gv_students, gv_annual, gv_transport, "gv")
            sr_fee_assignments = assign_fees_to_students(sr_students, sr_annual, sr_transport, "sr")

            # Create partial payments for ~30% of fee assignments
            def create_payments_for_assignments(assignments, prefix):
                receipt_counter = 1
                for fa in assignments:
                    if random.random() < 0.3:
                        # 1 or 2 payments
                        num_payments = 1 if random.random() < 0.5 else 2
                        remaining = float(fa.net_amount)
                        for i in range(num_payments):
                            if remaining <= 0:
                                break
                            pay_amount = remaining if i == num_payments - 1 else remaining * random.uniform(0.4, 0.7)
                            pay_amount = round(pay_amount, 2)
                            remaining -= pay_amount
                            FeePayment.objects.create(
                                assignment=fa,
                                amount=pay_amount,
                                mode=random.choice(["ONLINE", "CASH", "CARD"]),
                                receipt_number=f"{prefix.upper()}-RCPT-{receipt_counter:05d}",
                            )
                            receipt_counter += 1

            create_payments_for_assignments(gv_fee_assignments, "gv")
            create_payments_for_assignments(sr_fee_assignments, "sr")

        else:
            self.stdout.write(self.style.WARNING("Finance app/models not found; skipping finance seeding."))

        # ---------------------------------------------------------------------
        # 10. Communication: Announcements, Events, Leaves, Concerns
        # ---------------------------------------------------------------------
        if Announcement and Event:
            self.stdout.write("Creating announcements and events...")

            # Announcements for each school
            Announcement.objects.create(
                title="Welcome Back to School",
                message="New academic year has begun. Please check your class timetables.",
                created_by=gv_admin,
                target_class_section="All",
                is_for_parents=True,
                is_for_students=True,
            )
            Announcement.objects.create(
                title="PTM Scheduled",
                message="Parent–Teacher Meeting for high school classes is on 15 July at 9 AM.",
                created_by=gv_admin,
                target_class_section="9-10",
                is_for_parents=True,
                is_for_students=False,
            )

            Announcement.objects.create(
                title="Annual Day Celebration",
                message="Annual Day is scheduled for 20 December. Practices will start soon.",
                created_by=sr_admin,
                target_class_section="All",
                is_for_parents=True,
                is_for_students=True,
            )
            Announcement.objects.create(
                title="Bus Route Update",
                message="Sunrise school bus routes have changed. Check the notice board.",
                created_by=sr_admin,
                target_class_section="All",
                is_for_parents=True,
                is_for_students=True,
            )

            # Events & Holidays for both schools
            Event.objects.create(
                title="Science Fair",
                description="Science projects exhibition for grades 8–10.",
                date=date(2025, 8, 10),
                event_type="EVENT",
                created_by=gv_admin,
            )
            Event.objects.create(
                title="Independence Day",
                description="Flag hoisting and cultural programs.",
                date=date(2025, 8, 15),
                event_type="EVENT",
                created_by=gv_admin,
            )
            Event.objects.create(
                title="Christmas Holiday",
                description="School remains closed.",
                date=date(2025, 12, 25),
                event_type="HOLIDAY",
                created_by=gv_admin,
            )

            Event.objects.create(
                title="Math Olympiad",
                description="Inter-school Math competition.",
                date=date(2025, 9, 5),
                event_type="EVENT",
                created_by=sr_admin,
            )
            Event.objects.create(
                title="Founders Day",
                description="Special assembly and speeches.",
                date=date(2025, 11, 1),
                event_type="EVENT",
                created_by=sr_admin,
            )
            Event.objects.create(
                title="New Year Holiday",
                description="School remains closed.",
                date=date(2026, 1, 1),
                event_type="HOLIDAY",
                created_by=sr_admin,
            )
        else:
            self.stdout.write(self.style.WARNING("Announcement/Event models not found; skipping those."))

        # Leaves & Concerns (if models exist)
        if LeaveRequest and ParentConcern:
            self.stdout.write("Creating sample leave requests and parent concerns...")

            # pick a handful of students in GV 10A and SR 10A for demo
            sr_10A_students = sr_students_by_class.get(("10", "A"), [])

            sample_gv_students = gv_10A_students[:5] if len(gv_10A_students) >= 5 else gv_10A_students
            sample_sr_students = sr_10A_students[:5] if len(sr_10A_students) >= 5 else sr_10A_students

            # Leave requests
            for stu in sample_gv_students:
                LeaveRequest.objects.create(
                    student=stu,
                    start_date=date(2025, 7, 10),
                    end_date=date(2025, 7, 12),
                    reason="Family function",
                    status=random.choice(["PENDING", "APPROVED", "REJECTED"]),
                    reviewed_by=gv_admin,
                )

            for stu in sample_sr_students:
                LeaveRequest.objects.create(
                    student=stu,
                    start_date=date(2025, 7, 5),
                    end_date=date(2025, 7, 6),
                    reason="Fever and cold",
                    status=random.choice(["PENDING", "APPROVED", "REJECTED"]),
                    reviewed_by=sr_admin,
                )

            # Parent concerns
            for stu in sample_gv_students[:3]:
                ParentConcern.objects.create(
                    student=stu,
                    title="Homework Load",
                    message="The student is finding it difficult to cope with the daily homework load.",
                    status=random.choice(["OPEN", "IN_PROGRESS", "RESOLVED"]),
                    handled_by=gv_admin,
                )

            for stu in sample_sr_students[:3]:
                ParentConcern.objects.create(
                    student=stu,
                    title="Need Extra Help in Math",
                    message="Requesting additional support classes for Mathematics.",
                    status=random.choice(["OPEN", "IN_PROGRESS", "RESOLVED"]),
                    handled_by=sr_admin,
                )
        else:
            self.stdout.write(self.style.WARNING("LeaveRequest/ParentConcern not found; skipping those."))

        # ---------------------------------------------------------------------
        # 11. Train risk model & next-score models
        # ---------------------------------------------------------------------
        self.stdout.write("Training risk model & next-score models...")

        try:
            call_command("train_risk_model")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"train_risk_model failed (maybe not configured?): {e}"))

        try:
            call_command("train_next_scores")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"train_next_scores failed (maybe not configured?): {e}"))

        self.stdout.write(self.style.SUCCESS("Demo data seeding complete."))

        self.stdout.write(self.style.SUCCESS(
            "\nYou can now log in with for demo:\n"
            "  Management (Green Valley): username=gv_admin, password=Password123\n"
            "  Management (Sunrise):      username=sr_admin, password=Password123\n"
            "  Example Class Teacher:     one of gv_ct_10A / sr_ct_10A style usernames\n"
            "  Example Student (GV 10A):  one of gv_10A_xxx usernames (check in admin)\n"
        ))
