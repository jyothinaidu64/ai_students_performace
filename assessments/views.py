import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import AssessmentUploadForm
from students.models import Student
from .models import Subject, Assessment
from accounts.decorators import role_required

@role_required("MANAGEMENT", "CLASS_TEACHER")
def upload_assessments(request):
    if request.method == "POST":
        form = AssessmentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            df = pd.read_csv(request.FILES["file"])
            # Expect columns: admission_number, subject, exam_name, term, marks_obtained, max_marks, attendance_percent, assignments_completed
            created_count = 0
            for _, row in df.iterrows():
                try:
                    student = Student.objects.get(admission_number=row["admission_number"])
                    subject, _ = Subject.objects.get_or_create(name=row["subject"])
                    Assessment.objects.update_or_create(
                        student=student,
                        subject=subject,
                        exam_name=row["exam_name"],
                        term=row.get("term", ""),
                        defaults={
                            "marks_obtained": row["marks_obtained"],
                            "max_marks": row["max_marks"],
                            "attendance_percent": row.get("attendance_percent", 100.0),
                            "assignments_completed": row.get("assignments_completed", 0),
                        }
                    )
                    created_count += 1
                except Student.DoesNotExist:
                    continue
            messages.success(request, f"Uploaded/updated {created_count} assessments.")
            return redirect("upload_assessments")
    else:
        form = AssessmentUploadForm()
    return render(request, "assessments/upload.html", {"form": form})
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("OK")
