from django.db import models
from students.models import Student, SchoolClass

class Subject(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

# assessments/models.py

class Assessment(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE)
    subject = models.ForeignKey("assessments.Subject", on_delete=models.CASCADE)

    exam_name = models.CharField(max_length=100)
    exam_date = models.DateField()
    term = models.CharField(max_length=50, blank=True)

    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=100)

    attendance_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    assignments_completed = models.IntegerField(null=True, blank=True)

    # 👇 this is the new one
    topic = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Chapter / topic name (e.g. 'Quadratic Equations', 'Life Processes')",
    )

    def __str__(self):
        return f"{self.student} – {self.subject} – {self.exam_name}"


