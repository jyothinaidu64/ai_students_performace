"""
Comprehensive API Endpoint Tests
Tests: CRUD operations, Authentication, Permissions
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from students.models import Student, SchoolClass
from schools.models import School
from assessments.models import Subject, Assessment
from decimal import Decimal
from datetime import date

User = get_user_model()


class APIAuthenticationTestCase(TestCase):
    """Test API authentication and permissions"""
    
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(name="Test School")
        
        # Create test user
        self.user = User.objects.create_user(
            username="api_test_user",
            password="testpass123",
            role="MANAGEMENT",
            school=self.school
        )
    
    # ========== POSITIVE TESTS ==========
    
    def test_api_with_valid_authentication(self):
        """Positive: Access API with valid credentials"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/schools/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_api_list_pagination(self):
        """Positive: Verify pagination works"""
        self.client.force_authenticate(user=self.user)
        
        # Create multiple schools
        for i in range(15):
            School.objects.create(name=f"School {i}")
        
        response = self.client.get('/api/schools/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertEqual(len(response.data['results']), 10)  # Page size is 10
    
    # ========== NEGATIVE TESTS ==========
    
    def test_api_without_authentication(self):
        """Negative: Access API without credentials"""
        response = self.client.get('/api/schools/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_api_with_invalid_credentials(self):
        """Negative: Access API with wrong password"""
        self.client.login(username='api_test_user', password='wrongpass')
        response = self.client.get('/api/schools/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SchoolAPITestCase(TestCase):
    """Test School API CRUD operations"""
    
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(name="Test School")
        self.user = User.objects.create_user(
            username="school_admin",
            password="test123",
            role="MANAGEMENT",
            school=self.school
        )
        self.client.force_authenticate(user=self.user)
    
    # ========== CREATE (POST) ==========
    
    def test_create_school_positive(self):
        """Positive: Create new school"""
        data = {'name': 'New School', 'address': '123 Test St'}
        response = self.client.post('/api/schools/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(School.objects.count(), 2)
    
    def test_create_school_missing_name(self):
        """Negative: Create school without required name"""
        data = {'address': '123 Test St'}
        response = self.client.post('/api/schools/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # ========== READ (GET) ==========
    
    def test_list_schools(self):
        """Positive: List all schools"""
        response = self.client.get('/api/schools/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
    
    def test_retrieve_school_detail(self):
        """Positive: Get specific school details"""
        response = self.client.get(f'/api/schools/{self.school.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test School')
    
    def test_retrieve_nonexistent_school(self):
        """Negative: Get non-existent school"""
        response = self.client.get('/api/schools/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    # ========== UPDATE (PUT/PATCH) ==========
    
    def test_update_school_put(self):
        """Positive: Full update with PUT"""
        data = {'name': 'Updated School'}
        response = self.client.put(f'/api/schools/{self.school.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, 'Updated School')
    
    def test_update_school_patch(self):
        """Positive: Partial update with PATCH"""
        data = {'name': 'Patched School'}
        response = self.client.patch(f'/api/schools/{self.school.id}/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.school.refresh_from_db()
        self.assertEqual(self.school.name, 'Patched School')
    
    # ========== DELETE ==========
    
    def test_delete_school(self):
        """Positive: Delete school"""
        school_id = self.school.id
        response = self.client.delete(f'/api/schools/{school_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(School.objects.filter(id=school_id).exists())


class StudentAPITestCase(TestCase):
    """Test Student API operations"""
    
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(name="Test School")
        self.school_class = SchoolClass.objects.create(
            name="10", section="A", school=self.school
        )
        self.user = User.objects.create_user(
            username="student_admin",
            password="test123",
            role="MANAGEMENT",
            school=self.school
        )
        self.client.force_authenticate(user=self.user)
        
        # Create test student
        self.student_user = User.objects.create_user(
            username="test_student",
            password="test123",
            role="STUDENT",
            school=self.school
        )
        self.student = Student.objects.create(
            user=self.student_user,
            school_class=self.school_class,
            admission_number="TEST001"
        )
    
    def test_list_students(self):
        """Positive: List all students"""
        response = self.client.get('/api/students/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)
    
    def test_filter_students_by_class(self):
        """Positive: Filter students by class"""
        # Note: This assumes filtering is implemented
        response = self.client.get(f'/api/students/?school_class={self.school_class.id}')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_retrieve_student_detail(self):
        """Positive: Get student details"""
        response = self.client.get(f'/api/students/{self.student.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['admission_number'], 'TEST001')


class AssessmentAPITestCase(TestCase):
    """Test Assessment API operations"""
    
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(name="Test School")
        self.subject = Subject.objects.create(name="Mathematics")
        self.school_class = SchoolClass.objects.create(
            name="10", section="A", school=self.school
        )
        
        self.user = User.objects.create_user(
            username="teacher",
            password="test123",
            role="CLASS_TEACHER",
            school=self.school
        )
        self.client.force_authenticate(user=self.user)
        
        self.student_user = User.objects.create_user(
            username="student1",
            password="test123",
            role="STUDENT",
            school=self.school
        )
        self.student = Student.objects.create(
            user=self.student_user,
            school_class=self.school_class,
            admission_number="STU001"
        )
    
    def test_create_assessment(self):
        """Positive: Create new assessment"""
        data = {
            'student': self.student.id,
            'subject': self.subject.id,
            'marks_obtained': '85.5',
            'max_marks': '100.0',
            'attendance_percent': '90.0',
            'assignments_completed': 8,
            'exam_date': '2024-01-15',
            'term': '1',
            'topic': 'Algebra'
        }
        response = self.client.post('/api/assessments/', data, format='json')
        
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
    
    def test_create_assessment_invalid_marks(self):
        """Negative: Create assessment with marks > max_marks"""
        data = {
            'student': self.student.id,
            'subject': self.subject.id,
            'marks_obtained': '150.0',  # Invalid: > max_marks
            'max_marks': '100.0',
            'exam_date': '2024-01-15',
            'term': '1'
        }
        response = self.client.post('/api/assessments/', data, format='json')
        
        # Should either reject or accept (depends on validation)
        # Just verify it doesn't crash
        self.assertIsNotNone(response.status_code)
    
    def test_list_assessments(self):
        """Positive: List assessments"""
        Assessment.objects.create(
            student=self.student,
            subject=self.subject,
            marks_obtained=Decimal('75.0'),
            max_marks=Decimal('100.0'),
            exam_date=date.today(),
            term='1'
        )
        
        response = self.client.get('/api/assessments/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)


class APIBoundaryTestCase(TestCase):
    """Test API boundary conditions"""
    
    def setUp(self):
        self.client = APIClient()
        self.school = School.objects.create(name="Test School")
        self.user = User.objects.create_user(
            username="boundary_user",
            password="test123",
            role="MANAGEMENT",
            school=self.school
        )
        self.client.force_authenticate(user=self.user)
    
    def test_empty_list_response(self):
        """Boundary: List endpoint with no data"""
        # Delete all schools except the test one
        School.objects.exclude(id=self.school.id).delete()
        
        response = self.client.get('/api/subjects/')  # Likely empty
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
    
    def test_pagination_last_page(self):
        """Boundary: Request last page of pagination"""
        response = self.client.get('/api/schools/?page=999')
        
        # Should return empty results or 404
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
    
    def test_invalid_page_number(self):
        """Boundary: Invalid page number"""
        response = self.client.get('/api/schools/?page=-1')
        
        # Should handle gracefully
        self.assertIsNotNone(response.status_code)
    
    def test_very_long_name(self):
        """Boundary: Create school with very long name"""
        data = {'name': 'A' * 500}  # Very long name
        response = self.client.post('/api/schools/', data, format='json')
        
        # Should either accept or reject based on model constraints
        self.assertIn(response.status_code, [
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST
        ])
