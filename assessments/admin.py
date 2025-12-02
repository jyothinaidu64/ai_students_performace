# assessments/admin.py
from django.contrib import admin
from .models import Subject, Assessment


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "subject", "marks_obtained", "max_marks")
    list_filter = ("subject",)
    search_fields = ("student__first_name", "student__last_name", "student__admission_number")
