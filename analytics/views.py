# analytics/views.py

import csv

from django.http import HttpResponse
from django.shortcuts import render

from accounts.decorators import role_required
from students.models import SchoolClass, Student
from assessments.models import Assessment

from .ml_utils import (
    predict_student_risk,
    build_student_feature_dict,
    explain_risk,
    get_model_info,
    get_subject_averages_for_students,
    predict_next_score,
)


@role_required("CLASS_TEACHER")
def class_teacher_dashboard(request):
    # Filters from query params
    selected_risk = request.GET.get("risk", "all")       # 'all', 'high', 'low'
    sort_by = request.GET.get("sort_by", "risk_desc")    # default sort
    search_query = request.GET.get("search", "").strip()

    # The class this teacher is responsible for
    school_class = getattr(request.user, "class_teacher_of", None)

    if school_class is None:
        return render(request, "analytics/class_teacher_dashboard.html", {
            "school_class": None,
            "error": "No class is assigned to you yet.",
            "selected_risk": selected_risk,
            "sort_by": sort_by,
            "search_query": search_query,
            "rows": [],
            "high_count": 0,
            "low_count": 0,
            "total": 0,
        })

    students_qs = school_class.students.select_related("user")

    # Search by username or admission number
    if search_query:
        students_qs = (
            students_qs.filter(user__username__icontains=search_query)
            | students_qs.filter(admission_number__icontains=search_query)
        )

    rows = []
    high_count = 0
    low_count = 0

    for s in students_qs:
        pred = predict_student_risk(s)
        if not pred:
            continue

        label_str = "High" if pred["risk_label"] == 1 else "Low"

        # Risk filter
        if selected_risk == "high" and label_str != "High":
            continue
        if selected_risk == "low" and label_str != "Low":
            continue

        features = build_student_feature_dict(s)
        explanation, recs = explain_risk(s, features, pred)

        if label_str == "High":
            high_count += 1
        else:
            low_count += 1

        rows.append({
            "student": s,
            "risk_label": label_str,
            "risk_proba": pred["risk_proba"],
            "explanation": explanation,
            "recommendations": recs,
        })

    # Sorting options
    if sort_by == "name_asc":
        rows.sort(key=lambda r: r["student"].user.username.lower())
    elif sort_by == "name_desc":
        rows.sort(key=lambda r: r["student"].user.username.lower(), reverse=True)
    elif sort_by == "risk_asc":
        rows.sort(key=lambda r: r["risk_proba"])
    else:  # 'risk_desc' or unknown
        rows.sort(key=lambda r: r["risk_proba"], reverse=True)

    total = high_count + low_count
    insights = get_class_insights(school_class, rows)
    model_info = get_model_info()

    context = {
        "school_class": school_class,
        "rows": rows,
        "high_count": high_count,
        "low_count": low_count,
        "total": total,
        "selected_risk": selected_risk,
        "sort_by": sort_by,
        "search_query": search_query,
        "insights": insights,
        "model_info": model_info,
    }
    return render(request, "analytics/class_teacher_dashboard.html", context)


@role_required("CLASS_TEACHER")
def class_teacher_export_csv(request):
    """
    Export the class teacher's current filtered set of students as CSV.
    Uses same filters as class_teacher_dashboard.
    """
    selected_risk = request.GET.get("risk", "all")
    sort_by = request.GET.get("sort_by", "risk_desc")
    search_query = request.GET.get("search", "").strip()

    school_class = getattr(request.user, "class_teacher_of", None)
    if school_class is None:
        return HttpResponse("No class assigned to this teacher.", status=400)

    students_qs = school_class.students.select_related("user")

    if search_query:
        students_qs = (
            students_qs.filter(user__username__icontains=search_query)
            | students_qs.filter(admission_number__icontains=search_query)
        )

    rows = []

    for s in students_qs:
        pred = predict_student_risk(s)
        if not pred:
            continue

        label_str = "High" if pred["risk_label"] == 1 else "Low"

        if selected_risk == "high" and label_str != "High":
            continue
        if selected_risk == "low" and label_str != "Low":
            continue

        rows.append({
            "student": s,
            "risk_label": label_str,
            "risk_proba": pred["risk_proba"],
        })

    # sort
    if sort_by == "name_asc":
        rows.sort(key=lambda r: r["student"].user.username.lower())
    elif sort_by == "name_desc":
        rows.sort(key=lambda r: r["student"].user.username.lower(), reverse=True)
    elif sort_by == "risk_asc":
        rows.sort(key=lambda r: r["risk_proba"])
    else:  # risk_desc
        rows.sort(key=lambda r: r["risk_proba"], reverse=True)

    # CSV response
    response = HttpResponse(content_type="text/csv")
    filename = f"class_{school_class}_students_risk_export.csv".replace(" ", "_")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(["Username", "Admission No", "Class", "Risk Label", "Risk Probability"])

    for row in rows:
        s = row["student"]
        writer.writerow([
            s.user.username,
            s.admission_number,
            str(s.school_class),
            row["risk_label"],
            f"{row['risk_proba']:.4f}",
        ])

    return response


@role_required("MANAGEMENT")
def management_dashboard(request):
    # --- Read filters and sort from query params ---
    selected_class = request.GET.get("class", "all")
    selected_risk = request.GET.get("risk", "all")      # 'all', 'high', 'low'
    sort_by = request.GET.get("sort_by", "risk_desc")   # default
    search_query = request.GET.get("search", "").strip()

    # For the class filter dropdown
    classes = SchoolClass.objects.order_by("name", "section")

    # Base queryset: all students (we’ll filter in Python after risk calc)
    students_qs = Student.objects.select_related("school_class", "user")

    # Class filter
    if selected_class != "all":
        students_qs = students_qs.filter(school_class__id=selected_class)

    # Search filter (by username or admission number)
    if search_query:
        students_qs = (
            students_qs.filter(user__username__icontains=search_query)
            | students_qs.filter(admission_number__icontains=search_query)
        )

    subject_averages = get_subject_averages_for_students(students_qs)
    rows = []
    high_count = 0
    low_count = 0

    # Build rows with risk predictions
    for s in students_qs:
        pred = predict_student_risk(s)
        if not pred:
            continue

        label_str = "High" if pred["risk_label"] == 1 else "Low"

        # Risk filter (after prediction)
        if selected_risk == "high" and label_str != "High":
            continue
        if selected_risk == "low" and label_str != "Low":
            continue

        if label_str == "High":
            high_count += 1
        else:
            low_count += 1

        rows.append({
            "student": s,
            "risk_label": label_str,
            "risk_proba": pred["risk_proba"],
        })

    # --- Sorting ---
    if sort_by == "name_asc":
        rows.sort(key=lambda r: r["student"].user.username.lower())
    elif sort_by == "name_desc":
        rows.sort(key=lambda r: r["student"].user.username.lower(), reverse=True)
    elif sort_by == "class_asc":
        rows.sort(key=lambda r: (str(r["student"].school_class), r["student"].user.username.lower()))
    elif sort_by == "class_desc":
        rows.sort(
            key=lambda r: (str(r["student"].school_class), r["student"].user.username.lower()),
            reverse=True,
        )
    elif sort_by == "risk_asc":
        rows.sort(key=lambda r: r["risk_proba"])
    else:  # 'risk_desc' or unknown → default
        rows.sort(key=lambda r: r["risk_proba"], reverse=True)

    total = high_count + low_count
    high_pct = (high_count / total * 100) if total > 0 else 0.0
    low_pct = 100 - high_pct if total > 0 else 0.0
    model_info = get_model_info()

    context = {
        "rows": rows,
        "high_count": high_count,
        "low_count": low_count,
        "total": total,
        "high_pct": high_pct,
        "low_pct": low_pct,
        "classes": classes,
        "selected_class": selected_class,
        "selected_risk": selected_risk,
        "sort_by": sort_by,
        "search_query": search_query,
        "model_info": model_info,
        "subject_averages": subject_averages,
    }

    return render(request, "analytics/management_dashboard.html", context)


def health_check(request):
    return HttpResponse("OK")


@role_required("STUDENT")
def student_dashboard(request):
    user = request.user

    # Map logged-in user -> Student record, but be defensive
    try:
        student = Student.objects.get(user=user)
    except Student.DoesNotExist:
        return render(
            request,
            "analytics/no_student_profile.html",
            {"user": user},
            status=404,
        )

    # ---------- Risk prediction for this student ----------
    risk_info = {
        "available": False,
        "label": None,
        "proba": None,
        "explanation": None,
        "recommendations": [],
    }

    try:
        pred = predict_student_risk(student)
    except Exception:
        pred = None

    if pred:
        label_str = "High" if pred["risk_label"] == 1 else "Low"
        features = build_student_feature_dict(student)
        explanation, recs = explain_risk(student, features, pred)

        risk_info = {
            "available": True,
            "label": label_str,
            "proba": pred["risk_proba"],
            "explanation": explanation,
            "recommendations": recs,
        }

    # ---------- Assessments & subject stats ----------
    assessments = (
        Assessment.objects
        .filter(student=student)
        .select_related("subject")
        .order_by("exam_date")
    )

    # If no assessments yet, keep it simple
    if not assessments.exists():
        study_tips = build_study_coach_tips(student, [], risk_info)
        context = {
            "student": student,
            "subject_stats": [],
            "next_scores": [],
            "risk_info": risk_info,
            "study_tips": study_tips,
        }
        return render(request, "analytics/student_dashboard.html", context)

    # Collect unique subjects
    subjects = []
    seen_subject_ids = set()
    for a in assessments:
        if a.subject_id not in seen_subject_ids:
            seen_subject_ids.add(a.subject_id)
            subjects.append(a.subject)

    subject_stats = []  # list of dicts for template
    next_scores = []    # list of dicts for predictions

    for subj in subjects:
        subj_assessments = [a for a in assessments if a.subject_id == subj.id]
        if not subj_assessments:
            continue

        # Compute average mark percentage for this subject
        mark_pcts = []
        for a in subj_assessments:
            if a.max_marks:
                pct = (float(a.marks_obtained) / float(a.max_marks)) * 100.0
            else:
                pct = 0.0
            mark_pcts.append(pct)

        avg_pct = sum(mark_pcts) / len(mark_pcts) if mark_pcts else 0.0

        # Simple status buckets
        if avg_pct < 50:
            status = "Weak"
        elif avg_pct < 70:
            status = "Average"
        else:
            status = "Strong"

        subject_stats.append(
            {
                "subject_obj": subj,
                "subject_name": subj.name,
                "avg_pct": round(avg_pct, 1),
                "status": status,
            }
        )

        # ---------- Next exam score prediction for this subject ----------
        pred_score = predict_next_score(student, subj)
        if pred_score is not None:
            next_scores.append(
                {
                    "subject_obj": subj,
                    "subject_name": subj.name,
                    "predicted_score": round(pred_score, 1),
                }
            )

    # Sort lists by subject name
    subject_stats.sort(key=lambda row: row["subject_name"])
    next_scores.sort(key=lambda row: row["subject_name"])

    study_tips = build_study_coach_tips(student, subject_stats, risk_info)
    
    # Topic Mastery Heatmap
    from .topic_mastery_utils import build_heatmap_data
    heatmap_data = build_heatmap_data(student)
    
    # Weekly Study Plan
    from .study_plan_utils import generate_weekly_study_plan, get_study_recommendations
    study_plan = generate_weekly_study_plan(student)
    study_recommendations = get_study_recommendations(student)

    context = {
        "student": student,
        "subject_stats": subject_stats,
        "next_scores": next_scores,
        "risk_info": risk_info,
        "study_tips": study_tips,
        "heatmap_data": heatmap_data,
        "study_plan": study_plan,
        "study_recommendations": study_recommendations,
    }
    return render(request, "analytics/student_dashboard.html", context)


@role_required("MANAGEMENT")
def management_export_csv(request):
    """
    Export the currently filtered set of students as CSV.
    Uses same filters as management_dashboard.
    """
    selected_class = request.GET.get("class", "all")
    selected_risk = request.GET.get("risk", "all")   # 'all', 'high', 'low'
    sort_by = request.GET.get("sort_by", "risk_desc")
    search_query = request.GET.get("search", "").strip()

    students_qs = Student.objects.select_related("school_class", "user")

    if selected_class != "all":
        students_qs = students_qs.filter(school_class__id=selected_class)

    if search_query:
        students_qs = (
            students_qs.filter(user__username__icontains=search_query)
            | students_qs.filter(admission_number__icontains=search_query)
        )

    rows = []

    for s in students_qs:
        pred = predict_student_risk(s)
        if not pred:
            continue

        label_str = "High" if pred["risk_label"] == 1 else "Low"

        if selected_risk == "high" and label_str != "High":
            continue
        if selected_risk == "low" and label_str != "Low":
            continue

        rows.append({
            "student": s,
            "risk_label": label_str,
            "risk_proba": pred["risk_proba"],
        })

    # same sorting logic as dashboard
    if sort_by == "name_asc":
        rows.sort(key=lambda r: r["student"].user.username.lower())
    elif sort_by == "name_desc":
        rows.sort(key=lambda r: r["student"].user.username.lower(), reverse=True)
    elif sort_by == "class_asc":
        rows.sort(
            key=lambda r: (str(r["student"].school_class), r["student"].user.username.lower())
        )
    elif sort_by == "class_desc":
        rows.sort(
            key=lambda r: (str(r["student"].school_class), r["student"].user.username.lower()),
            reverse=True,
        )
    elif sort_by == "risk_asc":
        rows.sort(key=lambda r: r["risk_proba"])
    else:  # 'risk_desc'
        rows.sort(key=lambda r: r["risk_proba"], reverse=True)

    # --- Build CSV response ---
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="students_risk_export.csv"'

    writer = csv.writer(response)
    writer.writerow(["Username", "Admission No", "Class", "Risk Label", "Risk Probability"])

    for row in rows:
        s = row["student"]
        writer.writerow([
            s.user.username,
            s.admission_number,
            str(s.school_class),
            row["risk_label"],
            f"{row['risk_proba']:.4f}",
        ])

    return response


def get_class_insights(school_class, rows):
    """
    school_class: SchoolClass instance
    rows: list of dicts as built in class_teacher_dashboard (with risk info)
    Returns a list of {severity, text} items.
    """
    insights = []

    total = len(rows)
    high = sum(1 for r in rows if r["risk_label"] == "High")
    low = total - high

    if total > 0:
        high_pct = (high / total) * 100
        if high_pct >= 30:
            insights.append({
                "severity": "high",
                "text": f"{high} out of {total} students ({high_pct:.1f}%) are high risk. "
                        f"Consider scheduling remedial sessions."
            })
        elif high_pct > 0:
            insights.append({
                "severity": "medium",
                "text": f"{high} out of {total} students are high risk. Monitor them closely."
            })
        else:
            insights.append({
                "severity": "low",
                "text": "No high-risk students currently detected in this class."
            })

    insights.append({
        "severity": "info",
        "text": "Use the filters above to focus on high-risk students or sort by risk probability."
    })

    return insights


def build_study_coach_tips(student, subject_stats, risk_info):
    """
    Simple rule-based 'AI Study Coach'.
    Returns a list of short text tips based on subject statuses + risk.
    """
    tips = []

    if not subject_stats:
        tips.append(
            "Once your first few tests are recorded, I'll suggest a study plan based on your strengths and weaknesses."
        )
        return tips

    weak_subjects = [s for s in subject_stats if s["status"] == "Weak"]
    avg_subjects = [s for s in subject_stats if s["status"] == "Average"]
    strong_subjects = [s for s in subject_stats if s["status"] == "Strong"]

    weak_names = [s["subject_name"] for s in weak_subjects]
    avg_names = [s["subject_name"] for s in avg_subjects]
    strong_names = [s["subject_name"] for s in strong_subjects]

    risk_label = risk_info.get("label") if risk_info else None

    # Core advice by risk
    if risk_label == "High":
        tips.append(
            "Your overall exam risk is currently high. Focus on a consistent daily study routine of 45–60 minutes on weekdays."
        )
    elif risk_label == "Low":
        tips.append(
            "Your overall exam risk is low. Keep your current routine, but continue regular revision so your scores stay strong."
        )
    else:
        tips.append(
            "As more tests are recorded, your overall exam risk will be estimated. For now, focus on steady, regular practice."
        )

    # Subject-specific advice
    if weak_subjects:
        weak_str = ", ".join(weak_names)
        tips.append(
            f"You are struggling most with: {weak_str}. Start each study session by revising these subjects first."
        )
        tips.append(
            "For weak subjects, solve 3–5 short questions every day instead of only doing last-minute long sessions."
        )
    elif avg_subjects:
        avg_str = ", ".join(avg_names)
        tips.append(
            f"Your performance in {avg_str} is okay but can be improved. Focus on clarifying core concepts and practicing previous exam questions."
        )

    if strong_subjects:
        strong_str = ", ".join(strong_names)
        tips.append(
            f"You are strong in: {strong_str}. Use these subjects to boost your overall percentage—aim for nearly full marks in them."
        )

    # Generic time-management tip
    tips.append(
        "Create a weekly timetable that blocks 20–30 minutes for revision after school, and stick to it."
    )

    # Keep list short
    return tips[:5]

