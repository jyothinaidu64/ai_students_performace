"""
Topic Mastery & Study Plan Tests
Tests: Calculation logic, edge cases, data structures
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from students.models import Student, SchoolClass
from schools.models import School
from assessments.models import Subject, Assessment
from analytics.topic_mastery_utils import (
    calculate_topic_mastery,
    build_heatmap_data,
    get_weak_topics,
    get_mastery_level
)
from analytics.study_plan_utils import (
    generate_weekly_study_plan,
    identify_focus_topics,
    calculate_study_time_allocation,
    get_study_recommendations
)
from decimal import Decimal
from datetime import date, timedelta

User = get_user_model()


class TopicMasteryTestCase(TestCase):
    """Test topic mastery calculations"""
    
    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.subject = Subject.objects.create(name="Mathematics")
        self.school_class = SchoolClass.objects.create(
            name="10", section="A", school=self.school
        )
        self.user = User.objects.create_user(
            username="mastery_student",
            password="test123",
            role="STUDENT",
            school=self.school
        )
        self.student = Student.objects.create(
            user=self.user,
            school_class=self.school_class,
            admission_number="MAS001"
        )
    
    # ========== POSITIVE TESTS ==========
    
    def test_calculate_mastery_with_data(self):
        """Positive: Calculate mastery with multiple assessments"""
        # Create assessments for same topic
        for i in range(3):
            Assessment.objects.create(
                student=self.student,
                subject=self.subject,
                marks_obtained=Decimal('70.0'),
                max_marks=Decimal('100.0'),
                exam_date=date.today() - timedelta(days=i*10),
                term='1',
                topic='Algebra'
            )
        
        result = calculate_topic_mastery(self.student)
        
        self.assertIsNotNone(result)
        self.assertIn('Mathematics', result)
        self.assertIn('Algebra', result['Mathematics'])
        self.assertIn('mastery_score', result['Mathematics']['Algebra'])
    
    def test_mastery_level_classification(self):
        """Positive: Test mastery level categories"""
        self.assertEqual(get_mastery_level(30), 'Weak')
        self.assertEqual(get_mastery_level(60), 'Average')
        self.assertEqual(get_mastery_level(80), 'Strong')
    
    def test_build_heatmap_structure(self):
        """Positive: Build heatmap data structure"""
        # Create assessments
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('75.0'),
            max_marks=Decimal('100.0'),
            exam_date=date.today(),
            term='1',
            topic='Geometry'
        )
        
        heatmap = build_heatmap_data(self.student)
        
        self.assertIn('subjects', heatmap)
        self.assertIn('topics', heatmap)
        self.assertIn('matrix', heatmap)
        self.assertIn('details', heatmap)
    
    # ========== NEGATIVE TESTS ==========
    
    def test_mastery_no_assessments(self):
        """Negative: Calculate mastery with no data"""
        result = calculate_topic_mastery(self.student)
        
        self.assertEqual(result, {})
    
    def test_mastery_no_topics(self):
        """Negative: Assessments without topic field"""
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('80.0'),
            max_marks=Decimal('100.0'),
            exam_date=date.today(),
            term='1',
            topic=None  # No topic
        )
        
        result = calculate_topic_mastery(self.student)
        
        # Should return empty or handle gracefully
        self.assertIsInstance(result, dict)
    
    def test_weak_topics_empty(self):
        """Negative: Get weak topics when all strong"""
        # Create strong performance
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('95.0'),
            max_marks=Decimal('100.0'),
            exam_date=date.today(),
            term='1',
            topic='Calculus'
        )
        
        weak = get_weak_topics(self.student, threshold=60)
        
        self.assertEqual(len(weak), 0)
    
    # ========== BOUNDARY TESTS ==========
    
    def test_mastery_single_assessment(self):
        """Boundary: Mastery with only one assessment"""
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('50.0'),
            max_marks=Decimal('100.0'),
            exam_date=date.today(),
            term='1',
            topic='Trigonometry'
        )
        
        result = calculate_topic_mastery(self.student)
        
        self.assertIn('Mathematics', result)
        self.assertIn('Trigonometry', result['Mathematics'])
    
    def test_mastery_perfect_scores(self):
        """Boundary: All perfect scores"""
        for i in range(3):
            Assessment.objects.create(
                student=self.student,
                subject=self.subject,
                marks_obtained=Decimal('100.0'),
                max_marks=Decimal('100.0'),
                exam_date=date.today() - timedelta(days=i*5),
                term='1',
                topic='Perfect Topic'
            )
        
        result = calculate_topic_mastery(self.student)
        
        mastery = result['Mathematics']['Perfect Topic']['mastery_score']
        self.assertGreaterEqual(mastery, 90)  # Should be very high
    
    def test_mastery_zero_scores(self):
        """Boundary: All zero scores"""
        for i in range(3):
            Assessment.objects.create(
                student=self.student,
                subject=self.subject,
                marks_obtained=Decimal('0.0'),
                max_marks=Decimal('100.0'),
                exam_date=date.today() - timedelta(days=i*5),
                term='1',
                topic='Failing Topic'
            )
        
        result = calculate_topic_mastery(self.student)
        
        mastery = result['Mathematics']['Failing Topic']['mastery_score']
        self.assertLessEqual(mastery, 30)  # Should be very low


class StudyPlanTestCase(TestCase):
    """Test study plan generation"""
    
    def setUp(self):
        self.school = School.objects.create(name="Test School")
        self.subject = Subject.objects.create(name="Science")
        self.school_class = SchoolClass.objects.create(
            name="9", section="B", school=self.school
        )
        self.user = User.objects.create_user(
            username="plan_student",
            password="test123",
            role="STUDENT",
            school=self.school
        )
        self.student = Student.objects.create(
            user=self.user,
            school_class=self.school_class,
            admission_number="PLAN001"
        )
    
    # ========== POSITIVE TESTS ==========
    
    def test_generate_plan_with_weak_topics(self):
        """Positive: Generate plan for student with weak topics"""
        # Create weak performance
        for i in range(5):
            Assessment.objects.create(
                student=self.student,
                subject=self.subject,
                marks_obtained=Decimal('40.0'),
                max_marks=Decimal('100.0'),
                exam_date=date.today() - timedelta(days=i*7),
                term='1',
                topic=f'Weak Topic {i}'
            )
        
        plan = generate_weekly_study_plan(self.student)
        
        self.assertIsNotNone(plan)
        self.assertIn('week_start', plan)
        self.assertIn('daily_schedule', plan)
        self.assertIn('summary', plan)
        self.assertGreater(plan['summary']['total_hours'], 0)
    
    def test_study_recommendations(self):
        """Positive: Get study recommendations"""
        # Create mixed performance
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('45.0'),
            max_marks=Decimal('100.0'),
            exam_date=date.today(),
            term='1',
            topic='Chemistry'
        )
        
        recs = get_study_recommendations(self.student)
        
        self.assertIsInstance(recs, list)
        self.assertGreater(len(recs), 0)
    
    # ========== NEGATIVE TESTS ==========
    
    def test_plan_no_assessments(self):
        """Negative: Generate plan with no data"""
        plan = generate_weekly_study_plan(self.student)
        
        # Should return plan structure even if empty
        self.assertIsNotNone(plan)
        self.assertIn('daily_schedule', plan)
    
    def test_plan_all_strong_performance(self):
        """Negative: Generate plan when all topics strong"""
        # Create strong performance
        for i in range(3):
            Assessment.objects.create(
                student=self.student,
                subject=self.subject,
                marks_obtained=Decimal('90.0'),
                max_marks=Decimal('100.0'),
                exam_date=date.today() - timedelta(days=i*7),
                term='1',
                topic=f'Strong Topic {i}'
            )
        
        plan = generate_weekly_study_plan(self.student)
        
        # Should still generate plan (revision/maintenance)
        self.assertIsNotNone(plan)
    
    # ========== BOUNDARY TESTS ==========
    
    def test_plan_single_weak_topic(self):
        """Boundary: Plan with exactly one weak topic"""
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('30.0'),
            max_marks=Decimal('100.0'),
            exam_date=date.today(),
            term='1',
            topic='Single Weak'
        )
        
        plan = generate_weekly_study_plan(self.student)
        
        self.assertGreater(plan['summary']['weak_topics_count'], 0)
    
    def test_time_allocation_limits(self):
        """Boundary: Verify time allocation doesn't exceed limits"""
        # Create many weak topics
        for i in range(20):
            Assessment.objects.create(
                student=self.student,
                subject=self.subject,
                marks_obtained=Decimal('25.0'),
                max_marks=Decimal('100.0'),
                exam_date=date.today() - timedelta(days=i*3),
                term='1',
                topic=f'Topic {i}'
            )
        
        plan = generate_weekly_study_plan(self.student)
        
        # Total hours should be reasonable (not exceed 10h/week)
        self.assertLessEqual(plan['summary']['total_hours'], 10.0)
        
        # No single day should exceed 1.5 hours
        for day, tasks in plan['daily_schedule'].items():
            day_total = sum(task['duration'] for task in tasks)
            self.assertLessEqual(day_total, 1.5)
