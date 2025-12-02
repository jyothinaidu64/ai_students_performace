# analytics/management/commands/seed_demo_data.py

import random
from datetime import date, timedelta
from decimal import Decimal

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

User = get_user_model()


class Command(BaseCommand):
    help = "Wipe existing demo data and seed fresh end-to-end test data for all features."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("WIPING existing demo data..."))

        # Delete dependent models first
        TimetableEntry.objects.all().delete()
        Assessment.objects.all().delete()

        if NextExamPrediction:
            NextExamPrediction.objects.all().delete()
        if StudentRisk:
            StudentRisk.objects.all().delete()

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
            tagline="CBSE-aligned Analytics for AP Curriculum",
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
        # 2. Create CBSE-style Subjects (shared for simplicity)
        # ---------------------------------------------------------------------
        self.stdout.write("Creating subjects (CBSE-style core)...")

        core_subject_names = [
            "English",
            "Mathematics",
            "Science",
            "Social Science",
            "Telugu",
            "Hindi",
            "Computer Science",
        ]

        subjects = {}
        for name in core_subject_names:
            subjects[name] = Subject.objects.create(name=name)

        # Convenience aliases for existing code
        math = subjects["Mathematics"]
        sci = subjects["Science"]
        eng = subjects["English"]

        # ---------------------------------------------------------------------
        # 3. Create Users (Management, Teachers, Students)
        # ---------------------------------------------------------------------
        self.stdout.write("Creating users...")

        # Management users
        gv_admin = User.objects.create_user(
            username="gv_admin",
            email="gv_admin@example.com",
            password="Password123",
            role=User.Role.MANAGEMENT,
            school=gv_school,
        )

        sr_admin = User.objects.create_user(
            username="sr_admin",
            email="sr_admin@example.com",
            password="Password123",
            role=User.Role.MANAGEMENT,
            school=sr_school,
        )

        # Class teachers
        gv_ct_10 = User.objects.create_user(
            username="gv_ct_10A",
            email="gv_ct_10A@example.com",
            password="Password123",
            role=User.Role.CLASS_TEACHER,
            school=gv_school,
            first_name="Anjali",
            last_name="Sharma",
        )

        sr_ct_8 = User.objects.create_user(
            username="sr_ct_8A",
            email="sr_ct_8A@example.com",
            password="Password123",
            role=User.Role.CLASS_TEACHER,
            school=sr_school,
            first_name="Rohit",
            last_name="Verma",
        )

        # Subject teachers (for timetable)
        gv_math_teacher = User.objects.create_user(
            username="gv_math_teacher",
            email="gv_math_teacher@example.com",
            password="Password123",
            role=User.Role.TEACHER,
            school=gv_school,
            first_name="Meera",
            last_name="Patel",
        )
        gv_sci_teacher = User.objects.create_user(
            username="gv_sci_teacher",
            email="gv_sci_teacher@example.com",
            password="Password123",
            role=User.Role.TEACHER,
            school=gv_school,
            first_name="Rahul",
            last_name="Iyer",
        )
        gv_eng_teacher = User.objects.create_user(
            username="gv_eng_teacher",
            email="gv_eng_teacher@example.com",
            password="Password123",
            role=User.Role.TEACHER,
            school=gv_school,
            first_name="Divya",
            last_name="Rao",
        )

        # ---------------------------------------------------------------------
        # 4. Create Classes (LKG–10 A) for each school
        # ---------------------------------------------------------------------
        self.stdout.write("Creating classes...")

        class_names = ["LKG", "UKG"] + [f"{i}" for i in range(1, 10 + 1)]

        gv_classes = {}
        sr_classes = {}

        for name in class_names:
            gv_classes[name] = SchoolClass.objects.create(
                school=gv_school,
                name=name,
                section="A",
            )
            sr_classes[name] = SchoolClass.objects.create(
                school=sr_school,
                name=name,
                section="A",
            )

        # Assign class teachers to specific classes if your SchoolClass has such a field
        if hasattr(SchoolClass, "class_teacher"):
            gv_classes["10"].class_teacher = gv_ct_10
            gv_classes["10"].save()

            sr_classes["8"].class_teacher = sr_ct_8
            sr_classes["8"].save()

        # ---------------------------------------------------------------------
        # 5. Create Students (30 in 10A Green Valley, some in other classes)
        # ---------------------------------------------------------------------
        self.stdout.write("Creating students...")

        first_names = ["Ravi", "Sita", "Arjun", "Priya", "Kiran", "Lakshmi", "Vikram", "Neha"]
        last_names = ["Sharma", "Reddy", "Iyer", "Patel", "Nair", "Gupta", "Kumar", "Rao"]

        gv_10A = gv_classes["10"]
        students_gv_10 = []

        for roll in range(1, 31):
            fn = random.choice(first_names)
            ln = random.choice(last_names)
            username = f"gv10_{roll:02d}"
            user = User.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                password="Password123",
                role=User.Role.STUDENT,
                school=gv_school,
                first_name=fn,
                last_name=ln,
            )
            student = Student.objects.create(
                user=user,
                school_class=gv_10A,
                admission_number=f"GV10A-{roll:03d}",
                roll_number=str(roll),
            )
            students_gv_10.append(student)

        # A few Sunrise students in 8A
        sr_8A = sr_classes["8"]
        for roll in range(1, 11):
            fn = random.choice(first_names)
            ln = random.choice(last_names)
            username = f"sr8_{roll:02d}"
            user = User.objects.create_user(
                username=username,
                email=f"{username}@example.com",
                password="Password123",
                role=User.Role.STUDENT,
                school=sr_school,
                first_name=fn,
                last_name=ln,
            )
            Student.objects.create(
                user=user,
                school_class=sr_8A,
                admission_number=f"SR8A-{roll:03d}",
                roll_number=str(roll),
            )

        # ---------------------------------------------------------------------
        # 6. Create Assessments for a few key students (with CBSE-like topics)
        # ---------------------------------------------------------------------
        self.stdout.write("Creating assessments for ML & dashboard testing...")

        base_date = date(2025, 4, 1)

        # CBSE-like chapter/topic names for Class 10
        MATH_10_TOPICS = [
            "Real Numbers",
            "Polynomials",
            "Quadratic Equations",
            "Triangles",
            "Introduction to Trigonometry",
            "Statistics",
        ]

        SCI_10_TOPICS = [
            "Chemical Reactions",
            "Acids, Bases and Salts",
            "Metals and Non-metals",
            "Life Processes",
            "Control and Coordination",
            "Heredity and Evolution",
        ]

        ENG_10_TOPICS = [
            "Reading Comprehension",
            "Letter Writing",
            "Essay Writing",
            "Grammar",
            "Prose – First Flight",
            "Poetry – First Flight",
        ]

        def add_assessment(
            student,
            subject,
            exam_name,
            offset_days,
            marks,
            topics_list=None,
            max_marks=100,
            att=90,
            assignments=8,
        ):
            topic = random.choice(topics_list) if topics_list else None
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
                topic=topic,  # 👈 drives weak-topics analytics
            )

        # Pick 3 students in GV 10A with different profiles
        stu_weak = students_gv_10[0]   # high risk profile
        stu_medium = students_gv_10[1] # medium
        stu_strong = students_gv_10[2] # low risk

        # Weak student: low & unstable scores
        math_series_weak = [(0, 30), (30, 35), (60, 28), (90, 32)]
        for i, (offset, marks) in enumerate(math_series_weak, start=1):
            add_assessment(
                stu_weak,
                math,
                f"Math UT{i}",
                offset,
                marks,
                topics_list=MATH_10_TOPICS,
                att=75,
                assignments=4,
            )

        sci_series_weak = [(5, 40), (35, 42), (65, 38), (95, 39)]
        for i, (offset, marks) in enumerate(sci_series_weak, start=1):
            add_assessment(
                stu_weak,
                sci,
                f"Sci UT{i}",
                offset,
                marks,
                topics_list=SCI_10_TOPICS,
                att=78,
                assignments=5,
            )

        eng_series_weak = [(10, 45), (40, 48), (70, 44), (100, 46)]
        for i, (offset, marks) in enumerate(eng_series_weak, start=1):
            add_assessment(
                stu_weak,
                eng,
                f"Eng UT{i}",
                offset,
                marks,
                topics_list=ENG_10_TOPICS,
                att=80,
                assignments=6,
            )

        # Medium student: mid scores with slight improvement
        math_series_med = [(0, 55), (30, 58), (60, 60), (90, 62)]
        for i, (offset, marks) in enumerate(math_series_med, start=1):
            add_assessment(
                stu_medium,
                math,
                f"Math UT{i}",
                offset,
                marks,
                topics_list=MATH_10_TOPICS,
                att=88,
                assignments=7,
            )

        sci_series_med = [(5, 60), (35, 62), (65, 64), (95, 66)]
        for i, (offset, marks) in enumerate(sci_series_med, start=1):
            add_assessment(
                stu_medium,
                sci,
                f"Sci UT{i}",
                offset,
                marks,
                topics_list=SCI_10_TOPICS,
                att=90,
                assignments=8,
            )

        eng_series_med = [(10, 65), (40, 68), (70, 70), (100, 72)]
        for i, (offset, marks) in enumerate(eng_series_med, start=1):
            add_assessment(
                stu_medium,
                eng,
                f"Eng UT{i}",
                offset,
                marks,
                topics_list=ENG_10_TOPICS,
                att=92,
                assignments=9,
            )

        # Strong student: high and improving scores
        math_series_strong = [(0, 80), (30, 82), (60, 85), (90, 88)]
        for i, (offset, marks) in enumerate(math_series_strong, start=1):
            add_assessment(
                stu_strong,
                math,
                f"Math UT{i}",
                offset,
                marks,
                topics_list=MATH_10_TOPICS,
                att=95,
                assignments=10,
            )

        sci_series_strong = [(5, 78), (35, 80), (65, 83), (95, 86)]
        for i, (offset, marks) in enumerate(sci_series_strong, start=1):
            add_assessment(
                stu_strong,
                sci,
                f"Sci UT{i}",
                offset,
                marks,
                topics_list=SCI_10_TOPICS,
                att=96,
                assignments=10,
            )

        eng_series_strong = [(10, 82), (40, 85), (70, 88), (100, 90)]
        for i, (offset, marks) in enumerate(eng_series_strong, start=1):
            add_assessment(
                stu_strong,
                eng,
                f"Eng UT{i}",
                offset,
                marks,
                topics_list=ENG_10_TOPICS,
                att=97,
                assignments=10,
            )

        # ---------------------------------------------------------------------
        # 7. Create simple timetables for GV 10A
        # ---------------------------------------------------------------------
        self.stdout.write("Creating sample timetables...")

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
                    school_class=gv_10A,
                    day_of_week=DAY_MAP[d],
                    period=p,
                    subject=subject,
                    teacher=teacher,
                )

        # ---------------------------------------------------------------------
        # 8. Train risk model & next-score models
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
            "\nYou can now log in with:\n"
            "  Management (Green Valley): username=gv_admin, password=Password123\n"
            "  Management (Sunrise):      username=sr_admin, password=Password123\n"
            "  Class Teacher (GV 10A):    username=gv_ct_10A, password=Password123\n"
            "  Student (GV 10A #1):       username=gv10_01, password=Password123\n"
        ))
