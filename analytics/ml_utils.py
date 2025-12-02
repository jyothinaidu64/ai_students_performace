import pandas as pd
from pathlib import Path
import joblib

from django.conf import settings
from django.core.management.base import CommandError

from assessments.models import Assessment
from students.models import Student
from collections import defaultdict
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

MODEL_DIR = Path(settings.BASE_DIR) / "ml_models"
MODEL_DIR.mkdir(exist_ok=True)
import numpy as np
import joblib
import json
from pathlib import Path
from django.utils import timezone

import json
import numpy as np
from pathlib import Path
from django.utils import timezone
from django.core.management import CommandError
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib
from sklearn.ensemble import RandomForestRegressor
from assessments.models import Assessment
from students.models import Student
from django.db.models import Avg
from assessments.models import Assessment
from django.core.management.base import CommandError
import numpy as np
import pandas as pd
from pathlib import Path
import joblib

from django.utils import timezone
from django.core.management.base import CommandError

from assessments.models import Assessment, Subject
from students.models import Student

PREDICTOR_DIR = Path(__file__).resolve().parent / "artifacts" / "next_score"
PREDICTOR_DIR.mkdir(parents=True, exist_ok=True)


# Make sure MODEL_DIR is already defined above, e.g.:
# MODEL_DIR = Path(settings.BASE_DIR) / "ml_models"

def build_training_dataframe() -> pd.DataFrame:
    """
    Build one row per student with engineered features + synthetic label.
    If there is no usable data, returns an empty DataFrame with correct columns.
    """
    cols = [
        "student_id",
        "avg_marks_pct",
        "avg_attendance_percent",
        "avg_assignments_completed",
        "marks_variance",
        "last_test_score",
        "risk_label",
    ]

    data = []

    # Pre-fetch assessments to avoid lots of DB hits
    assessments_qs = Assessment.objects.select_related("student")

    for student in Student.objects.all():
        stu_assessments = assessments_qs.filter(student=student)
        if not stu_assessments.exists():
            # no assessment data for this student → skip
            continue

        df = pd.DataFrame(
            list(
                stu_assessments.values(
                    "marks_obtained",
                    "max_marks",
                    "attendance_percent",
                    "assignments_completed",
                )
            )
        )
        # Convert Decimal columns to float to avoid TypeError during arithmetic
        df["marks_obtained"] = df["marks_obtained"].astype(float)
        df["max_marks"] = df["max_marks"].astype(float)
        df["attendance_percent"] = df["attendance_percent"].astype(float)
        df["assignments_completed"] = df["assignments_completed"].astype(float)

        if df.empty:
            continue

        # Compute marks % per row
        marks_pct_series = (df["marks_obtained"] / df["max_marks"]) * 100

        avg_marks_pct = marks_pct_series.mean()
        avg_attendance_percent = df["attendance_percent"].mean()
        avg_assignments_completed = df["assignments_completed"].mean()
        marks_variance = marks_pct_series.var()  # variance of marks percentage
        last_test_score = marks_pct_series.iloc[-1]

        # Simple synthetic label for now:
        #   1 = high risk, 0 = low risk
        risk_label = 1 if (avg_marks_pct < 40 or avg_attendance_percent < 75) else 0

        data.append(
            {
                "student_id": student.id,
                "avg_marks_pct": avg_marks_pct,
                "avg_attendance_percent": avg_attendance_percent,
                "avg_assignments_completed": avg_assignments_completed,
                "marks_variance": marks_variance,
                "last_test_score": last_test_score,
                "risk_label": risk_label,
            }
        )

    if not data:
        # no usable records, but return an empty DF with the expected columns
        return pd.DataFrame(columns=cols)

    return pd.DataFrame(data, columns=cols)

import math

def build_student_feature_dict(student):
    """
    Compute the same kind of features we use for training,
    but for a single student, as a plain dict.
    """
    qs = Assessment.objects.filter(student=student).order_by("exam_date")
    if not qs.exists():
        return {
            "avg_marks_pct": 0.0,
            "avg_attendance_percent": 0.0,
            "avg_assignments_completed": 0.0,
            "marks_variance": 0.0,
            "last_test_score": 0.0,
        }

    marks = [float(a.marks_obtained) / float(a.max_marks) * 100.0 for a in qs]
    attendance = [float(a.attendance_percent or 0) for a in qs]
    assignments = [float(a.assignments_completed or 0) for a in qs]

    avg_marks_pct = sum(marks) / len(marks) if marks else 0.0
    avg_attendance_percent = sum(attendance) / len(attendance) if attendance else 0.0
    avg_assignments_completed = sum(assignments) / len(assignments) if assignments else 0.0

    # simple variance of marks
    if len(marks) > 1:
        mean = avg_marks_pct
        marks_variance = sum((m - mean) ** 2 for m in marks) / (len(marks) - 1)
    else:
        marks_variance = 0.0

    last_test_score = marks[-1] if marks else 0.0

    return {
        "avg_marks_pct": avg_marks_pct,
        "avg_attendance_percent": avg_attendance_percent,
        "avg_assignments_completed": avg_assignments_completed,
        "marks_variance": marks_variance,
        "last_test_score": last_test_score,
    }


def explain_risk(student, features_dict, pred_dict):
    """
    Given features + predicted risk, return (explanation_text, recommendations_list).
    This is rule-based for now (no external AI).
    """
    reasons = []
    recs = []

    avg_marks = features_dict.get("avg_marks_pct", 0) or 0
    attendance = features_dict.get("avg_attendance_percent", 0) or 0
    assignments = features_dict.get("avg_assignments_completed", 0) or 0
    variance = features_dict.get("marks_variance", 0) or 0
    last_score = features_dict.get("last_test_score", 0) or 0

    # Reasons
    if avg_marks < 50:
        reasons.append("low average marks")
    elif avg_marks > 75:
        reasons.append("strong average marks")

    if attendance < 80:
        reasons.append("low attendance")
    elif attendance > 90:
        reasons.append("excellent attendance")

    if assignments < 3:
        reasons.append("few assignments completed")
    elif assignments > 4:
        reasons.append("consistent assignment completion")

    if variance > 400:  # roughly > 20 marks std dev
        reasons.append("high variation in test scores")
    elif 0 < variance < 100:
        reasons.append("stable test scores")

    if last_score < 50:
        reasons.append("recent test score was poor")
    elif last_score > 80:
        reasons.append("recent test score was strong")

    label = "High" if pred_dict["risk_label"] == 1 else "Low"

    if reasons:
        explanation = f"{label} risk because of " + ", ".join(reasons) + "."
    else:
        explanation = f"{label} risk based on recent performance."

    # Recommendations (simple rules)
    if pred_dict["risk_label"] == 1:
        # high risk
        recs.append("Schedule a one-on-one discussion with the student.")
        recs.append("Share a weekly study plan and track completion.")
        if avg_marks < 60:
            recs.append("Focus on core subjects where marks are below 60%.")
        if attendance < 85:
            recs.append("Engage parents regarding attendance improvement.")
        if assignments < 3:
            recs.append("Set a target of completing at least 3 assignments per subject this month.")
    else:
        # low risk
        recs.append("Maintain current study routine and monitor periodically.")
        if avg_marks > 80:
            recs.append("Encourage participation in competitions or olympiads.")
        if attendance > 90:
            recs.append("Recognize good attendance in class announcements.")

    return explanation, recs


def train_model():
    """
    Trains the Logistic Regression model on all available students/assessments,
    saves model + scaler, writes model_info.json and metrics.
    Returns training accuracy.
    """
    df = build_training_dataframe()

    if df.empty:
        raise CommandError(
            "No training data available. "
            "Make sure you have Students and Assessments in the database "
            "before running train_risk_model."
        )

    features = [
        "avg_marks_pct",
        "avg_attendance_percent",
        "avg_assignments_completed",
        "marks_variance",
        "last_test_score",
    ]

    X = df[features].fillna(0)
    y = df["risk_label"]

    # Basic safety check: at least 2 classes
    if len(set(y)) < 2:
        raise CommandError("Training data must contain at least two classes for risk_label.")

    # Extra explicit check with numpy (optional but clearer in error message)
    unique_classes = np.unique(y)
    if len(unique_classes) < 2:
        raise CommandError(
            f"Need at least 2 classes for training, but found only: {unique_classes}. "
            "Adjust your data or labelling rule so that some students are high risk (1) "
            "and others are low risk (0)."
        )

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train model
    model = LogisticRegression(max_iter=1000)
    model.fit(X_scaled, y)

    # Evaluate on training data
    y_pred = model.predict(X_scaled)
    acc = float(accuracy_score(y, y_pred))
    report = classification_report(y, y_pred, output_dict=True)

    # Persist artifacts
    MODEL_DIR = Path(__file__).resolve().parent / "artifacts"
    MODEL_DIR.mkdir(exist_ok=True, parents=True)

    joblib.dump(model, MODEL_DIR / "model.joblib")
    joblib.dump(scaler, MODEL_DIR / "scaler.joblib")

    # JSON for dashboards / UI
    model_info = {
        "last_trained_at": timezone.now().isoformat(),
        "accuracy": acc,
        "n_samples": int(len(df)),
        "n_features": len(features),
    }
    with open(MODEL_DIR / "model_info.json", "w") as f:
        json.dump(model_info, f, indent=2)

    # Extra metrics as joblib (if you want to inspect later)
    joblib.dump(
        {"accuracy": acc, "classification_report": report},
        MODEL_DIR / "model_metrics.joblib",
    )

    return acc






def predict_student_risk(student: Student):
    """
    Load the trained model and scaler, compute features for a single student,
    and return risk probability + label.
    Returns None if the student has no assessments or model files are missing.
    """
    from pathlib import Path
    from django.conf import settings

    model_path = MODEL_DIR / "model.joblib"
    scaler_path = MODEL_DIR / "scaler.joblib"

    # If model is not trained yet, safely return None
    if not model_path.exists() or not scaler_path.exists():
        return None

    try:
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
    except Exception:
        # corrupted files etc.
        return None

    qs = Assessment.objects.filter(student=student)
    if not qs.exists():
        return None

    df = pd.DataFrame(
        list(
            qs.values(
                "marks_obtained",
                "max_marks",
                "attendance_percent",
                "assignments_completed",
            )
        )
    )

    if df.empty:
        return None

    # Convert Decimal columns to float
    df["marks_obtained"] = df["marks_obtained"].astype(float)
    df["max_marks"] = df["max_marks"].astype(float)
    df["attendance_percent"] = df["attendance_percent"].astype(float)
    df["assignments_completed"] = df["assignments_completed"].astype(float)

    marks_pct_series = (df["marks_obtained"] / df["max_marks"]) * 100

    avg_marks_pct = marks_pct_series.mean()
    avg_attendance_percent = df["attendance_percent"].mean()
    avg_assignments_completed = df["assignments_completed"].mean()
    marks_variance = marks_pct_series.var()
    last_test_score = marks_pct_series.iloc[-1]

    features = np.array(
        [
            [
                avg_marks_pct,
                avg_attendance_percent,
                avg_assignments_completed,
                marks_variance,
                last_test_score,
            ]
        ]
    )

    try:
        X_scaled = scaler.transform(features)
        prob = float(model.predict_proba(X_scaled)[0][1])
        label = int(model.predict(X_scaled)[0])
    except Exception:
        return None

    return {
        "risk_proba": prob,        # 0–1
        "risk_label": label,       # 0 = low risk, 1 = high risk
    }




def get_student_subject_snapshot(student):
    """
    Returns a list of dicts:
    [
      {"subject": "Math", "avg_pct": 72.5, "status": "Average"},
      ...
    ]
    """
    qs = Assessment.objects.filter(student=student)
    if not qs.exists():
        return []

    # Group marks by subject
    subject_marks = defaultdict(list)

    for a in qs:
        if a.max_marks:
            pct = (float(a.marks_obtained) / float(a.max_marks)) * 100.0
            subject_marks[a.subject.name].append(pct)

    snapshot = []
    for subj_name, marks in subject_marks.items():
        if not marks:
            continue
        avg_pct = sum(marks) / len(marks)

        # Simple classification thresholds
        if avg_pct < 50:
            status = "Weak"
        elif avg_pct < 75:
            status = "Average"
        else:
            status = "Strong"

        snapshot.append({
            "subject": subj_name,
            "avg_pct": avg_pct,
            "status": status,
        })

    # Sort by weakest first
    snapshot.sort(key=lambda x: x["avg_pct"])
    return snapshot

def get_model_info():
    """
    Returns a dict with last_trained_at, accuracy, n_samples, n_features,
    or None if file missing or invalid.
    """
    MODEL_DIR = Path(__file__).resolve().parent / "artifacts"
    info_path = MODEL_DIR / "model_info.json"
    if not info_path.exists():
        return None

    try:
        with open(info_path, "r") as f:
            data = json.load(f)
        return data
    except Exception:
        return None


def get_subject_averages_for_students(students_qs):
    """
    Given a queryset of Student, compute average % per subject across all their assessments.
    Returns a list:
    [
      {"subject": "Math", "avg_pct": 68.5},
      {"subject": "Science", "avg_pct": 72.1},
      ...
    ]
    """
    # Preload assessments for all students in one query
    assessments = Assessment.objects.filter(student__in=students_qs).select_related("subject")

    if not assessments.exists():
        return []

    subject_marks = defaultdict(list)

    for a in assessments:
        if a.max_marks:
            pct = (float(a.marks_obtained) / float(a.max_marks)) * 100.0
            subject_marks[a.subject.name].append(pct)

    results = []
    for subj_name, marks in subject_marks.items():
        if not marks:
            continue
        avg_pct = sum(marks) / len(marks)
        results.append({
            "subject": subj_name,
            "avg_pct": avg_pct,
        })

    # Sort weakest → strongest
    results.sort(key=lambda x: x["avg_pct"])
    return results



def build_next_score_training_dataframe(min_assessments_per_student_subject: int = 3):
    qs = (
        Assessment.objects
        .select_related("student", "subject")
        .order_by("student_id", "subject_id", "exam_date")  # ✅ exam_date
    )

    if not qs.exists():
        raise CommandError("No assessments found for building next-score training data.")

    rows = []
    current_key = None
    current_marks = []
    current_attendances = []
    current_dates = []

    def flush_sequence(student_id, subject_id, marks, attendances, dates):
        n = len(marks)
        if n < min_assessments_per_student_subject:
            return
        for i in range(1, n):
            history = marks[:i]
            last_mark = history[-1]
            avg_mark = float(np.mean(history))
            marks_var = float(np.var(history)) if len(history) > 1 else 0.0
            history_att = attendances[:i]
            avg_att = float(np.mean(history_att)) if history_att else 0.0
            rows.append(
                {
                    "student_id": student_id,
                    "subject_id": subject_id,
                    "avg_mark": avg_mark,
                    "last_mark": last_mark,
                    "marks_var": marks_var,
                    "avg_attendance": avg_att,
                    "next_mark": float(marks[i]),
                }
            )

    for a in qs:
        key = (a.student_id, a.subject_id)
        if key != current_key:
            if current_key is not None:
                flush_sequence(current_key[0], current_key[1], current_marks, current_attendances, current_dates)
            current_key = key
            current_marks = []
            current_attendances = []
            current_dates = []

        # Convert Decimal to float before arithmetic
        marks_obtained = float(a.marks_obtained)
        max_marks = float(a.max_marks)
        mark_pct = (marks_obtained / max_marks) * 100.0 if max_marks else 0.0
        att_pct = getattr(a, "attendance_percent", 0.0) or 0.0

        current_marks.append(mark_pct)
        current_attendances.append(att_pct)
        current_dates.append(a.exam_date)

    if current_key is not None:
        flush_sequence(current_key[0], current_key[1], current_marks, current_attendances, current_dates)

    if not rows:
        raise CommandError("Not enough sequential assessments to build next-score training data.")

    return pd.DataFrame(rows)


def train_next_score_models():
    df = build_next_score_training_dataframe()

    features = ["avg_mark", "last_mark", "marks_var", "avg_attendance"]
    target = "next_mark"

    subjects = Subject.objects.all()
    if not subjects.exists():
        raise CommandError("No subjects found when training next-score models.")

    results = []
    for subject in subjects:
        df_sub = df[df["subject_id"] == subject.id]
        if len(df_sub) < 10:   # you can lower this to 5 or 3 for testing
            continue

        X = df_sub[features].values
        y = df_sub[target].values

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_scaled, y)
        score = model.score(X_scaled, y)

        joblib.dump(model, PREDICTOR_DIR / f"subject_{subject.id}_regressor.joblib")
        joblib.dump(scaler, PREDICTOR_DIR / f"subject_{subject.id}_scaler.joblib")

        results.append(
            {
                "subject_id": subject.id,
                "subject_name": subject.name,
                "n_samples": len(df_sub),
                "train_r2": float(score),
            }
        )

    info = {
        "trained_at": timezone.now().isoformat(),
        "subjects": results,
    }
    joblib.dump(info, PREDICTOR_DIR / "next_score_info.joblib")
    return info


def predict_next_score(student: Student, subject: Subject):
    qs = (
        Assessment.objects
        .filter(student=student, subject=subject)
        .order_by("exam_date")
    )
    if qs.count() < 2:
        return None

    marks = []
    atts = []
    for a in qs:
        mark_pct = (float(a.marks_obtained) / float(a.max_marks)) * 100.0 if a.max_marks else 0.0
        att_pct = getattr(a, "attendance_percent", 0.0) or 0.0
        marks.append(mark_pct)
        atts.append(att_pct)

    last_mark = marks[-1]
    avg_mark = float(np.mean(marks))
    marks_var = float(np.var(marks)) if len(marks) > 1 else 0.0
    avg_att = float(np.mean(atts))

    X = np.array([[avg_mark, last_mark, marks_var, avg_att]])

    model_path = PREDICTOR_DIR / f"subject_{subject.id}_regressor.joblib"
    scaler_path = PREDICTOR_DIR / f"subject_{subject.id}_scaler.joblib"
    if not model_path.exists() or not scaler_path.exists():
        return None

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)

    X_scaled = scaler.transform(X)
    y_pred = model.predict(X_scaled)[0]
    return float(y_pred)
