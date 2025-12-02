# students/models.py
from django.db import models
from django.conf import settings
from schools.models import School

User = settings.AUTH_USER_MODEL


class SchoolClass(models.Model):
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="classes",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=20)  # '1', '2', 'LKG', etc.
    section = models.CharField(max_length=2, blank=True, null=True)

    class_teacher = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"role": "CLASS_TEACHER"},
        related_name="class_teacher_of",
    )

    def __str__(self):
        sec = self.section or ""
        return f"{self.name}{sec}"

    class Meta:
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        ordering = ["school__name", "name", "section"]


class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "STUDENT"},
        related_name="student_profile",
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        related_name="students",
    )

    photo = models.ImageField(
        upload_to="student_photos/",
        blank=True,
        null=True,
        help_text="Student's photo for profile & report cards.",
    )

    roll_number = models.CharField(max_length=20)
    admission_number = models.CharField(max_length=30, unique=True)

    date_of_birth = models.DateField(null=True, blank=True)

    # ---------- Convenience helpers ----------

    @property
    def full_name(self):
        first = getattr(self.user, "first_name", "") or ""
        last = getattr(self.user, "last_name", "") or ""
        full = f"{first} {last}".strip()
        return full or self.user.username

    def __str__(self):
        base = self.full_name
        if self.school_class:
            return f"{base} ({self.admission_number}) – {self.school_class}"
        return f"{base} ({self.admission_number})"

    class Meta:
        ordering = ["school_class__name", "roll_number"]
