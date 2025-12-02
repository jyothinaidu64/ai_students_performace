from django.urls import path
from . import views
from . import export_views

urlpatterns = [
    path("dashboard/", views.management_dashboard, name="management_dashboard"),
    path("dashboard/export/", views.management_export_csv, name="management_export_csv"),
    path("dashboard/export-pdf/", export_views.export_management_pdf, name="management_export_pdf"),
    path("student/", views.student_dashboard, name="student_dashboard"),
    path("student/export-pdf/", export_views.export_student_pdf, name="student_export_pdf"),
    path("class/", views.class_teacher_dashboard, name="class_teacher_dashboard"),
    path("class/export/", views.class_teacher_export_csv, name="class_teacher_export_csv"),
    path("class/export-pdf/", export_views.export_class_teacher_pdf, name="class_teacher_export_pdf"),
]

