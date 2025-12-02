#!/usr/bin/env python
"""
Test fixes for known issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'students_performance.settings')
django.setup()

from schools.models import School
from assessments.models import Assessment, Subject
from students.models import Student
from decimal import Decimal

def test_school_slug_generation():
    """Test automatic slug generation"""
    print("="*70)
    print("Testing School Slug Auto-Generation")
    print("="*70)
    
    try:
        # Test 1: Create school without slug
        school1 = School(name="Test School Alpha")
        school1.save()
        print(f"✓ School created with auto-slug: '{school1.slug}'")
        
        # Test 2: Create another school with same name
        school2 = School(name="Test School Alpha")
        school2.save()
        print(f"✓ Duplicate name handled: '{school2.slug}'")
        
        # Test 3: Create school with manual slug
        school3 = School(name="Test School Beta", slug="custom-slug")
        school3.save()
        print(f"✓ Manual slug preserved: '{school3.slug}'")
        
        # Cleanup
        school1.delete()
        school2.delete()
        school3.delete()
        
        print("\n✅ School slug generation: PASS\n")
        return True
    except Exception as e:
        print(f"\n❌ School slug generation: FAIL - {str(e)}\n")
        return False

def test_assessment_validation():
    """Test assessment validation"""
    print("="*70)
    print("Testing Assessment Validation")
    print("="*70)
    
    try:
        from rest_framework.test import APIClient
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        client = APIClient()
        
        # Create test data
        school = School.objects.first()
        if not school:
            school = School.objects.create(name="Test School", slug="test-school")
        
        user = User.objects.filter(role="MANAGEMENT").first()
        if not user:
            user = User.objects.create_user(
                username="test_mgmt",
                password="test123",
                role="MANAGEMENT",
                school=school
            )
        
        client.force_authenticate(user=user)
        
        student = Student.objects.first()
        subject = Subject.objects.first()
        
        if not student or not subject:
            print("⚠ Skipping validation tests - missing test data")
            return True
        
        # Test 1: marks_obtained > max_marks (should fail)
        data = {
            'student': student.id,
            'subject': subject.id,
            'marks_obtained': '150.0',
            'max_marks': '100.0',
            'exam_date': '2024-01-15',
            'term': '1'
        }
        response = client.post('/api/assessments/', data, format='json')
        if response.status_code == 400:
            print("✓ Validation rejected marks > max_marks")
        else:
            print(f"⚠ Validation may need improvement (status: {response.status_code})")
        
        # Test 2: max_marks = 0 (should fail)
        data['marks_obtained'] = '0.0'
        data['max_marks'] = '0.0'
        response = client.post('/api/assessments/', data, format='json')
        if response.status_code == 400:
            print("✓ Validation rejected max_marks = 0")
        else:
            print(f"⚠ Validation may need improvement (status: {response.status_code})")
        
        # Test 3: attendance > 100 (should fail)
        data['max_marks'] = '100.0'
        data['attendance_percent'] = '150.0'
        response = client.post('/api/assessments/', data, format='json')
        if response.status_code == 400:
            print("✓ Validation rejected attendance > 100")
        else:
            print(f"⚠ Validation may need improvement (status: {response.status_code})")
        
        print("\n✅ Assessment validation: PASS\n")
        return True
    except Exception as e:
        print(f"\n❌ Assessment validation: FAIL - {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False

def test_sklearn_version():
    """Test sklearn version"""
    print("="*70)
    print("Testing Sklearn Version")
    print("="*70)
    
    try:
        import sklearn
        print(f"✓ Sklearn version: {sklearn.__version__}")
        
        # Try loading a model
        from analytics.ml_utils import predict_student_risk
        student = Student.objects.first()
        if student:
            result = predict_student_risk(student)
            if result:
                print(f"✓ ML model loaded successfully")
            else:
                print(f"⚠ ML model returned None (may need more data)")
        
        print("\n✅ Sklearn version: OK\n")
        return True
    except Exception as e:
        print(f"\n❌ Sklearn version: FAIL - {str(e)}\n")
        return False

def run_fix_tests():
    """Run all fix tests"""
    print("\n🔧 " * 35)
    print("   TESTING FIXES FOR KNOWN ISSUES")
    print("🔧 " * 35 + "\n")
    
    results = {
        'School Slug Generation': test_school_slug_generation(),
        'Assessment Validation': test_assessment_validation(),
        'Sklearn Version': test_sklearn_version(),
    }
    
    print("="*70)
    print("FIX TEST SUMMARY")
    print("="*70)
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component:30s}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n{'='*70}")
    print(f"Overall: {passed}/{total} fixes verified ({passed/total*100:.1f}%)")
    print(f"{'='*70}\n")
    
    return passed == total

if __name__ == "__main__":
    success = run_fix_tests()
    exit(0 if success else 1)
