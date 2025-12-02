# students/admin.py
from django.contrib import admin
from .models import SchoolClass, Student


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ("name", "section")
    list_filter = ("name",)
    search_fields = ("name", "section")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("admission_number", "full_name", "school_class")
    list_filter = ("school_class",)
    search_fields = ("admission_number", "first_name", "last_name")

    def full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    full_name.short_description = "Full Name"
    full_name.admin_order_field = "user__first_name"
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("user", "school_class")
        return qs
    def first_name(self, obj):
        return obj.user.first_name
    def last_name(self, obj):
        return obj.user.last_name
    first_name.admin_order_field = "user__first_name"

