from django.db import models
from students.models import Student
from assessments.models import Subject


class NextExamPrediction(models.Model):
    """
    Stores simplest 'next exam score' predictions per student+subject.
    This is optional, but useful if you want to audit predictions later.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="next_exam_predictions")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="next_exam_predictions")

    predicted_score = models.FloatField()
    model_version = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "subject")

    def __str__(self):
        return f"Pred: {self.student} – {self.subject} = {self.predicted_score:.1f}"
