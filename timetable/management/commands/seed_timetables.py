from django.core.management.base import BaseCommand
from django.db import transaction

from timetable.models import TimetableEntry
from students.models import SchoolClass
from assessments.models import Subject
from accounts.models import User


class Command(BaseCommand):
    help = "Generate sample weekly timetables for all classes (LKG–10) using existing subjects and teacher users."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding timetables..."))

        # Fetch all classes
        classes = SchoolClass.objects.order_by("name", "section")
        if not classes.exists():
            self.stdout.write(self.style.ERROR("No SchoolClass records found. Seed classes first."))
            return

        # Fetch all subjects
        subjects = list(Subject.objects.order_by("name"))
        if len(subjects) == 0:
            self.stdout.write(self.style.ERROR("No subjects found. Seed subjects first."))
            return

        # Fetch teacher users
        teachers = list(User.objects.filter(role=User.Role.TEACHER).order_by("username"))
        if len(teachers) == 0:
            self.stdout.write(self.style.ERROR("No teacher users found (role=TEACHER). Seed teachers first."))
            return

        DAYS = [0, 1, 2, 3, 4]  # Monday–Friday
        PERIODS = [1, 2, 3, 4, 5, 6]  # 6 periods per day

        # Simple rotation:
        # For each class, rotate subjects and teachers so timetable looks varied
        with transaction.atomic():
            TimetableEntry.objects.all().delete()
            self.stdout.write(self.style.WARNING("Deleted existing TimetableEntry records."))

            teacher_count = len(teachers)
            subject_count = len(subjects)

            for idx, school_class in enumerate(classes):
                self.stdout.write(f"Building timetable for class: {school_class}")

                # Offset per class so schedules differ a bit
                class_subject_offset = idx % subject_count
                class_teacher_offset = idx % teacher_count

                for day_index, day_code in enumerate(DAYS):
                    for period_index, period in enumerate(PERIODS):
                        # Pick subject via rotating index
                        subj_idx = (day_index * len(PERIODS) + period_index + class_subject_offset) % subject_count
                        subject = subjects[subj_idx]

                        # Pick teacher via rotating index
                        teacher_idx = (day_index * len(PERIODS) + period_index + class_teacher_offset) % teacher_count
                        teacher = teachers[teacher_idx]

                        TimetableEntry.objects.create(
                            school_class=school_class,
                            day_of_week=day_code,
                            period=period,
                            subject=subject,
                            teacher=teacher,
                        )

            self.stdout.write(self.style.SUCCESS("✔ Timetables seeded successfully for all classes."))
