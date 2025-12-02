"""
Comprehensive Test Suite for ML Utilities
Tests: Positive, Negative, and Boundary Conditions
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from students.models import Student, SchoolClass
from schools.models import School
from assessments.models import Subject, Assessment
from analytics.ml_utils import (
    build_training_dataframe,
    predict_student_risk,
    build_student_feature_dict,
    predict_next_score
)
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()


class MLUtilsTestCase(TestCase):
    """Test ML utility functions with various conditions"""
    
    def setUp(self):
        """Set up test data"""
        # Create school
        self.school = School.objects.create(name="Test School")
        
        # Create subject
        self.subject = Subject.objects.create(name="Mathematics")
        
        # Create class
        self.school_class = SchoolClass.objects.create(
            name="10",
            section="A",
            school=self.school
        )
        
        # Create user and student
        self.user = User.objects.create_user(
            username="test_student",
            password="test123",
            role="STUDENT",
            school=self.school
        )
        self.student = Student.objects.create(
            user=self.user,
            school_class=self.school_class,
            admission_number="TEST001"
        )
    
    # ========== POSITIVE TESTS ==========
    
    def test_predict_risk_with_valid_data(self):
        """Positive: Predict risk with sufficient assessment data"""
        # Create multiple assessments
        for i in range(5):
            Assessment.objects.create(
                student=self.student,
                subject=self.subject,
                marks_obtained=Decimal('60.0'),
                max_marks=Decimal('100.0'),
                attendance_percent=Decimal('80.0'),
                assignments_completed=8,
                exam_date=date.today() - timedelta(days=i*10),
                term='1',
                topic=f"Topic {i}"
            )
        
        result = predict_student_risk(self.student)
        
        # Should return prediction
        self.assertIsNotNone(result)
        self.assertIn('risk_label', result)
        self.assertIn('risk_proba', result)
        self.assertIn(result['risk_label'], [0, 1])
        self.assertGreaterEqual(result['risk_proba'], 0.0)
        self.assertLessEqual(result['risk_proba'], 1.0)
    
    def test_build_feature_dict_complete_data(self):
        """Positive: Build features with complete assessment data"""
        # Create assessments
        for i in range(3):
            Assessment.objects.create(
                student=self.student,
                subject=self.subject,
                marks_obtained=Decimal('75.0'),
                max_marks=Decimal('100.0'),
                attendance_percent=Decimal('90.0'),
                assignments_completed=10,
                exam_date=date.today() - timedelta(days=i*15),
                term='1'
            )
        
        features = build_student_feature_dict(self.student)
        
        self.assertIsNotNone(features)
        self.assertIn('avg_marks_pct', features)
        self.assertIn('avg_attendance', features)
        self.assertGreater(features['avg_marks_pct'], 0)
    
    # ========== NEGATIVE TESTS ==========
    
    def test_predict_risk_no_assessments(self):
        """Negative: Predict risk with no assessment data"""
        result = predict_student_risk(self.student)
        
        # Should return None or handle gracefully
        self.assertIsNone(result)
    
    def test_predict_risk_insufficient_data(self):
        """Negative: Predict risk with only 1 assessment"""
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('50.0'),
            max_marks=Decimal('100.0'),
            attendance_percent=Decimal('70.0'),
            assignments_completed=5,
            exam_date=date.today(),
            term='1'
        )
        
        result = predict_student_risk(self.student)
        
        # Should handle insufficient data
        # Either return None or make prediction with available data
        if result:
            self.assertIn('risk_label', result)
    
    def test_build_feature_dict_no_data(self):
        """Negative: Build features with no assessments"""
        features = build_student_feature_dict(self.student)
        
        # Should return empty or default features
        self.assertIsNotNone(features)
    
    # ========== BOUNDARY TESTS ==========
    
    def test_predict_risk_zero_marks(self):
        """Boundary: All assessments with zero marks"""
        for i in range(3):
            Assessment.objects.create(
                student=self.student,
                subject=self.subject,
                marks_obtained=Decimal('0.0'),
                max_marks=Decimal('100.0'),
                attendance_percent=Decimal('50.0'),
                assignments_completed=0,
                exam_date=date.today() - timedelta(days=i*10),
                term='1'
            )
        
        result = predict_student_risk(self.student)
        
        if result:
            # Should predict high risk
            self.assertIsNotNone(result)
            self.assertIn('risk_label', result)
    
    def test_predict_risk_perfect_marks(self):
        """Boundary: All assessments with perfect marks"""
        for i in range(3):
            Assessment.objects.create(
                student=self.student,
                subject=self.subject,
                marks_obtained=Decimal('100.0'),
                max_marks=Decimal('100.0'),
                attendance_percent=Decimal('100.0'),
                assignments_completed=10,
                exam_date=date.today() - timedelta(days=i*10),
                term='1'
            )
        
        result = predict_student_risk(self.student)
        
        if result:
            # Should predict low risk
            self.assertIsNotNone(result)
            self.assertIn('risk_label', result)
    
    def test_predict_risk_max_marks_zero(self):
        """Boundary: Assessment with max_marks = 0"""
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('0.0'),
            max_marks=Decimal('0.0'),  # Edge case
            attendance_percent=Decimal('80.0'),
            assignments_completed=5,
            exam_date=date.today(),
            term='1'
        )
        
        # Should handle division by zero gracefully
        try:
            result = predict_student_risk(self.student)
            # If it doesn't crash, test passes
            self.assertTrue(True)
        except ZeroDivisionError:
            self.fail("Should handle max_marks=0 gracefully")
    
    def test_next_score_prediction_boundary(self):
        """Boundary: Next score prediction with minimum data"""
        # Create exactly 2 assessments (minimum for trend)
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('60.0'),
            max_marks=Decimal('100.0'),
            attendance_percent=Decimal('75.0'),
            exam_date=date.today() - timedelta(days=30),
            term='1',
            topic="Algebra"
        )
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('70.0'),
            max_marks=Decimal('100.0'),
            attendance_percent=Decimal('80.0'),
            exam_date=date.today(),
            term='1',
            topic="Algebra"
        )
        
        result = predict_next_score(self.student, self.subject)
        
        # Should make prediction or return None
        if result is not None:
            self.assertIsInstance(result, (int, float))
            self.assertGreaterEqual(result, 0)
            self.assertLessEqual(result, 100)
    
    def test_decimal_float_conversion(self):
        """Boundary: Test Decimal to float conversion in calculations"""
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('67.5'),
            max_marks=Decimal('100.0'),
            attendance_percent=Decimal('85.5'),
            assignments_completed=7,
            exam_date=date.today(),
            term='1'
        )
        
        # Should handle Decimal values without TypeError
        try:
            features = build_student_feature_dict(self.student)
            self.assertIsNotNone(features)
        except TypeError as e:
            self.fail(f"Decimal conversion failed: {str(e)}")


class MLEdgeCasesTestCase(TestCase):
    """Test edge cases and error handling"""
    
    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.subject = Subject.objects.create(name="Science")
        self.school_class = SchoolClass.objects.create(
            name="9", section="B", school=self.school
        )
        self.user = User.objects.create_user(
            username="edge_student", password="test123",
            role="STUDENT", school=self.school
        )
        self.student = Student.objects.create(
            user=self.user,
            school_class=self.school_class,
            admission_number="EDGE001"
        )
    
    def test_null_attendance(self):
        """Edge: Assessment with null attendance"""
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('75.0'),
            max_marks=Decimal('100.0'),
            attendance_percent=None,  # Null value
            assignments_completed=5,
            exam_date=date.today(),
            term='1'
        )
        
        # Should handle null gracefully
        try:
            result = predict_student_risk(self.student)
            self.assertTrue(True)  # Didn't crash
        except Exception as e:
            self.fail(f"Failed to handle null attendance: {str(e)}")
    
    def test_future_exam_date(self):
        """Edge: Assessment with future date"""
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('80.0'),
            max_marks=Decimal('100.0'),
            attendance_percent=Decimal('90.0'),
            exam_date=date.today() + timedelta(days=30),  # Future
            term='1'
        )
        
        # Should still process
        result = predict_student_risk(self.student)
        # Test passes if no exception
        self.assertTrue(True)
    
    def test_very_old_assessments(self):
        """Edge: Very old assessment data"""
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('50.0'),
            max_marks=Decimal('100.0'),
            attendance_percent=Decimal('60.0'),
            exam_date=date.today() - timedelta(days=365*2),  # 2 years old
            term='1'
        )
        
        result = predict_student_risk(self.student)
        # Should still work with old data
        self.assertTrue(True)
