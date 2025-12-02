from rest_framework import viewsets
from .models import TimetableEntry
from .serializers import TimetableEntrySerializer

class TimetableEntryViewSet(viewsets.ModelViewSet):
    queryset = TimetableEntry.objects.all()
    serializer_class = TimetableEntrySerializer
