# PDF Export Views

from django.http import FileResponse, HttpResponse
from accounts.decorators import role_required
from students.models import Student
from assessments.models import Assessment
from .ml_utils import predict_student_risk
from .pdf_utils import create_student_performance_pdf, create_class_report_pdf, create_management_report_pdf



@role_required("STUDENT")
def export_student_pdf(request):
    """Export student performance report as PDF"""
    user = request.user
    
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        return HttpResponse("Student profile not found", status=404)
    
    # Get dashboard data
    from .topic_mastery_utils import build_heatmap_data
    from .study_plan_utils import generate_weekly_study_plan
    
    assessments = Assessment.objects.filter(student=student).select_related("subject")
    
    # Build subject stats
    subject_stats = []
    subjects_seen = set()
    for a in assessments:
        if a.subject_id not in subjects_seen:
            subjects_seen.add(a.subject_id)
            subj_assessments = [x for x in assessments if x.subject_id == a.subject_id]
            mark_pcts = [(float(x.marks_obtained) / float(x.max_marks)) * 100.0 
                        for x in subj_assessments if x.max_marks]
            if mark_pcts:
                avg_pct = sum(mark_pcts) / len(mark_pcts)
                status = "Weak" if avg_pct < 50 else "Average" if avg_pct < 70 else "Strong"
                subject_stats.append({
                    'subject_name': a.subject.name,
                    'avg_pct': avg_pct,
                    'status': status
                })
    
    # Risk info
    from .ml_utils import predict_student_risk, build_student_feature_dict, explain_risk
    pred = predict_student_risk(student)
    risk_info = None
    if pred:
        label_str = "High" if pred["risk_label"] == 1 else "Low"
        features = build_student_feature_dict(student)
        explanation, recs = explain_risk(student, features, pred)
        risk_info = {
            'available': True,
            'label': label_str,
            'proba': pred['risk_proba'],
            'explanation': explanation,
            'recommendations': recs
        }
    
    heatmap_data = build_heatmap_data(student)
    study_plan = generate_weekly_study_plan(student)
    
    # Generate PDF
    pdf_buffer = create_student_performance_pdf(student, subject_stats, risk_info, heatmap_data, study_plan)
    
    response = FileResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="student_report_{student.user.username}.pdf"'
    return response


@role_required("CLASS_TEACHER")
def export_class_teacher_pdf(request):
    """Export class teacher dashboard as PDF"""
    school_class = getattr(request.user, "class_teacher_of", None)
    
    if school_class is None:
        return HttpResponse("No class assigned", status=400)
    
    students_qs = school_class.students.select_related("user")
    
    rows = []
    for s in students_qs:
        pred = predict_student_risk(s)
        if pred:
            label_str = "High" if pred["risk_label"] == 1 else "Low"
            rows.append({
                'student': s,
                'risk_label': label_str,
                'risk_proba': pred['risk_proba']
            })
    
    pdf_buffer = create_class_report_pdf(school_class, rows)
    
    response = FileResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="class_report_{school_class}.pdf"'
    return response


@role_required("MANAGEMENT")
def export_management_pdf(request):
    """Export management dashboard as PDF"""
    students_qs = Student.objects.select_related("school_class", "user")
    
    rows = []
    for s in students_qs:
        pred = predict_student_risk(s)
        if pred:
            label_str = "High" if pred["risk_label"] == 1 else "Low"
            rows.append({
                'student': s,
                'risk_label': label_str,
                'risk_proba': pred['risk_proba']
            })
    
    pdf_buffer = create_management_report_pdf(rows)
    
    response = FileResponse(pdf_buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="management_report.pdf"'
    return response
