from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "school", "is_staff", "is_superuser")
    list_filter = ("role", "school", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email")
    ordering = ("username",)

    fieldsets = (
        ("Account", {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("School & Role", {"fields": ("school", "role")}),
        ("Profile & Signature", {"fields": ("profile_photo", "teacher_signature")}),  # 👈 uses real model fields
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            "Create User",
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "school", "role", "profile_photo"),
            },
        ),
    )
