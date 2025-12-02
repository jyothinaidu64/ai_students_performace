# timetable/admin.py
from django.contrib import admin
from .models import TimetableEntry


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ("school_class", "day_of_week", "period", "subject", "teacher")
    list_filter = ("school_class", "day_of_week", "teacher", "subject")
    search_fields = ("school_class__name", "teacher__username", "subject__name")
