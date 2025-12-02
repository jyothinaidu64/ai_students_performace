from django.contrib.auth.models import AbstractUser
from django.db import models
from schools.models import School
class User(AbstractUser):
    class Role(models.TextChoices):
        MANAGEMENT = "MANAGEMENT", "Management"
        CLASS_TEACHER = "CLASS_TEACHER", "Class Teacher"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
        help_text="School this user belongs to."
    )
    profile_photo = models.ImageField(
        upload_to="user_photos/",
        blank=True,
        null=True,
        help_text="Profile photo for this user.",
    )

    teacher_signature = models.ImageField(
        upload_to="teacher_signatures/",
        blank=True,
        null=True,
        help_text="Signature image for teachers, shown on marks cards.",
    )
    def __str__(self):
        return f"{self.username} ({self.role})"

