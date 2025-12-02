from django.urls import path
from . import views

app_name = "communication"

urlpatterns = [
    path("announcements/", views.my_announcements_view, name="my_announcements"),
    path("announcements/admin/", views.admin_announcements_view, name="my_announcements_admin"),
    path("announcements/", views.my_announcements_view, name="my_announcements"),
    path("calendar/", views.event_calendar_view, name="calendar"),
    path("calendar/admin/", views.event_calendar_admin, name="calendar_admin"),
    path("events/new/", views.event_create, name="event_create"),
    path("leave/new/", views.create_leave_request, name="create_leave"),
    path("leave/mine/", views.my_leave_requests, name="my_leaves"),
    path("concern/new/", views.create_concern, name="create_concern"),
    path("concern/mine/", views.my_concerns, name="my_concerns"),
    path("leave/mine/", views.my_leave_requests, name="my_leaves"),
    path(
        "leave/class/<str:class_section>/",
        views.class_leave_requests,
        name="class_leave_requests",
    ),
    path("concerns/all/", views.all_concerns, name="all_concerns"),
    path(
    "announcements/new/",
    views.announcement_create,
    name="announcement_create",
)

]
