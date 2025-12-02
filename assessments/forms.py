from django import forms

class AssessmentUploadForm(forms.Form):
    file = forms.FileField()
