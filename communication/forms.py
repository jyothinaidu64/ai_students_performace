# communication/forms.py
from django import forms
from .models import LeaveRequest, Announcement, Event, ParentConcern
class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["start_date", "end_date", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }
# communication/forms.py
from .models import ParentConcern

class ParentConcernForm(forms.ModelForm):
    class Meta:
        model = ParentConcern
        fields = ["title", "message"]
class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ["title", "message", "target_class_section", "is_for_parents", "is_for_students"]
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["title", "description", "date", "start_time", "end_time", "event_type"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }
