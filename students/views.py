from django.http import HttpResponse

def health_check(request):
    return HttpResponse("OK")
from django.shortcuts import render
from accounts.decorators import role_required
from students.models import SchoolClass, Student
from analytics.ml_utils import predict_student_risk
