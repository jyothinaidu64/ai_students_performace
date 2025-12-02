#!/usr/bin/env python
"""
Comprehensive Project Audit & Test Script
Reviews all functions, tests functionality, identifies issues
"""
import os
import django
import sys
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'students_performance.settings')
django.setup()

from django.contrib.auth import get_user_model
from students.models import Student, SchoolClass
from schools.models import School
from assessments.models import Subject, Assessment
from analytics.ml_utils import predict_student_risk, predict_next_score
from analytics.topic_mastery_utils import calculate_topic_mastery, build_heatmap_data
from analytics.study_plan_utils import generate_weekly_study_plan
from analytics.pdf_utils import create_student_performance_pdf

User = get_user_model()

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_models():
    """Test all model counts and basic operations"""
    print_section("MODEL AUDIT")
    
    models_to_check = [
        ('Users', User),
        ('Schools', School),
        ('Classes', SchoolClass),
        ('Students', Student),
        ('Subjects', Subject),
        ('Assessments', Assessment),
    ]
    
    for name, model in models_to_check:
        count = model.objects.count()
        print(f"✓ {name:20s}: {count:5d} records")
    
    return True

def test_ml_functions():
    """Test ML utility functions"""
    print_section("ML FUNCTIONS AUDIT")
    
    try:
        student = Student.objects.first()
        if not student:
            print("⚠ No students found - skipping ML tests")
            return False
        
        # Test risk prediction
        print("\n1. Testing Risk Prediction...")
        risk = predict_student_risk(student)
        if risk:
            print(f"   ✓ Risk prediction working: {risk['risk_label']}, prob={risk['risk_proba']:.3f}")
        else:
            print("   ⚠ Risk prediction returned None (may need more data)")
        
        # Test next score prediction
        print("\n2. Testing Next Score Prediction...")
        subject = Subject.objects.first()
        if subject:
            next_score = predict_next_score(student, subject)
            if next_score:
                print(f"   ✓ Next score prediction working: {next_score:.1f}%")
            else:
                print("   ⚠ Next score prediction returned None")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_topic_mastery():
    """Test topic mastery functions"""
    print_section("TOPIC MASTERY AUDIT")
    
    try:
        student = Student.objects.first()
        if not student:
            print("⚠ No students found")
            return False
        
        print("\n1. Testing Topic Mastery Calculation...")
        mastery = calculate_topic_mastery(student)
        if mastery:
            total_topics = sum(len(topics) for topics in mastery.values())
            print(f"   ✓ Calculated mastery for {len(mastery)} subjects, {total_topics} topics")
        else:
            print("   ⚠ No mastery data (student may not have topic-based assessments)")
        
        print("\n2. Testing Heatmap Data Builder...")
        heatmap = build_heatmap_data(student)
        print(f"   ✓ Heatmap: {len(heatmap['subjects'])} subjects × {len(heatmap['topics'])} topics")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_study_plan():
    """Test study plan generation"""
    print_section("STUDY PLAN AUDIT")
    
    try:
        student = Student.objects.first()
        if not student:
            print("⚠ No students found")
            return False
        
        print("\n1. Testing Study Plan Generation...")
        plan = generate_weekly_study_plan(student)
        if plan:
            print(f"   ✓ Generated plan: {plan['summary']['total_hours']}h total")
            print(f"   ✓ Targeting {plan['summary']['weak_topics_count']} weak topics")
            print(f"   ✓ Covering {plan['summary']['subjects_covered']} subjects")
        else:
            print("   ⚠ No study plan generated")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_pdf_export():
    """Test PDF generation"""
    print_section("PDF EXPORT AUDIT")
    
    try:
        student = Student.objects.first()
        if not student:
            print("⚠ No students found")
            return False
        
        print("\n1. Testing PDF Generation...")
        subject_stats = [{'subject_name': 'Test', 'avg_pct': 75.0, 'status': 'Average'}]
        risk_info = {'available': True, 'label': 'Low', 'proba': 0.3}
        
        pdf_buffer = create_student_performance_pdf(student, subject_stats, risk_info)
        size = len(pdf_buffer.getvalue())
        print(f"   ✓ PDF generated: {size} bytes")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_views():
    """Test view accessibility"""
    print_section("VIEWS AUDIT")
    
    from django.test import Client
    client = Client()
    
    views_to_test = [
        ('Login Page', '/accounts/login/'),
        ('API Root', '/api/'),
    ]
    
    for name, url in views_to_test:
        try:
            response = client.get(url)
            status = "✓" if response.status_code in [200, 302, 403] else "❌"
            print(f"{status} {name:30s}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {name:30s}: Error - {str(e)}")
    
    return True

def check_code_quality():
    """Check for common code issues"""
    print_section("CODE QUALITY CHECKS")
    
    issues = []
    
    # Check for TODO/FIXME comments
    print("\n1. Checking for TODO/FIXME comments...")
    todo_count = 0
    for root, dirs, files in os.walk('.'):
        # Skip venv and migrations
        if '.venv' in root or 'migrations' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if 'TODO' in line or 'FIXME' in line:
                                todo_count += 1
                except:
                    pass
    
    if todo_count > 0:
        print(f"   ⚠ Found {todo_count} TODO/FIXME comments")
    else:
        print(f"   ✓ No TODO/FIXME comments found")
    
    # Check for print statements (should use logging)
    print("\n2. Checking for print statements...")
    print_count = 0
    for root, dirs, files in os.walk('.'):
        if '.venv' in root or 'migrations' in root or '__pycache__' in root or 'tests' in root:
            continue
        for file in files:
            if file.endswith('.py') and file != 'manage.py':
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'print(' in content:
                            print_count += 1
                except:
                    pass
    
    if print_count > 5:
        print(f"   ⚠ Found print() in {print_count} files (consider using logging)")
    else:
        print(f"   ✓ Minimal print statements found")
    
    return True

def run_audit():
    """Run complete audit"""
    print("\n" + "🔍 " * 35)
    print("   COMPREHENSIVE PROJECT AUDIT")
    print("🔍 " * 35)
    
    results = {
        'Models': test_models(),
        'ML Functions': test_ml_functions(),
        'Topic Mastery': test_topic_mastery(),
        'Study Plan': test_study_plan(),
        'PDF Export': test_pdf_export(),
        'Views': test_views(),
        'Code Quality': check_code_quality(),
    }
    
    print_section("AUDIT SUMMARY")
    
    for component, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{component:20s}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n{'='*70}")
    print(f"Overall: {passed}/{total} components passed ({passed/total*100:.1f}%)")
    print(f"{'='*70}\n")
    
    if passed == total:
        print("🎉 All systems operational!")
    else:
        print("⚠️  Some issues detected - review output above")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_audit()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fatal error during audit: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
