from django.db import models
from students.models import SchoolClass
from assessments.models import Subject
from django.conf import settings

User = settings.AUTH_USER_MODEL

class TeacherSubject(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={"role": "TEACHER"})
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

class TimetableEntry(models.Model):
    DAY_CHOICES = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
    ]

    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="timetable_entries")
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    period = models.IntegerField()  # 1..6 etc.
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("school_class", "day_of_week", "period")
        ordering = ["school_class", "day_of_week", "period"]

    def __str__(self):
        return f"{self.school_class} - {self.get_day_of_week_display()} P{self.period}: {self.subject}"
