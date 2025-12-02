from django.urls import path
from . import views

urlpatterns = [
    path("classes/", views.timetable_class_list, name="timetable_class_list"),
    path("class/<int:class_id>/", views.timetable_class_view, name="timetable_class_view"),
    path("class/<int:class_id>/regenerate/", views.timetable_regenerate_for_class, name="timetable_regenerate_for_class"),
    path("teacher/me/", views.teacher_timetable_view, name="teacher_timetable_view"),
]

