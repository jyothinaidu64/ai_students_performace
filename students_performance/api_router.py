from rest_framework import routers
from accounts.api_views import UserViewSet
from schools.api_views import SchoolViewSet
from students.api_views import StudentViewSet, SchoolClassViewSet
from assessments.api_views import SubjectViewSet, AssessmentViewSet
from timetable.api_views import TimetableEntryViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'schools', SchoolViewSet)
router.register(r'classes', SchoolClassViewSet)
router.register(r'students', StudentViewSet)
router.register(r'subjects', SubjectViewSet)
router.register(r'assessments', AssessmentViewSet)
router.register(r'timetable', TimetableEntryViewSet)

urlpatterns = router.urls

