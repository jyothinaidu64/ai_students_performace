#!/usr/bin/env python
"""
Test PDF export functionality
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'students_performance.settings')
django.setup()

from students.models import Student
from analytics.pdf_utils import create_student_performance_pdf, create_class_report_pdf, create_management_report_pdf
from analytics.ml_utils import predict_student_risk

def test_pdf_generation():
    print("=" * 70)
    print("Testing PDF Export Functionality")
    print("=" * 70)
    
    # Test 1: Student PDF
    print("\nTest 1: Student Performance PDF")
    print("-" * 70)
    try:
        student = Student.objects.filter(user__username='gv10_01').first()
        if student:
            # Mock data
            subject_stats = [
                {'subject_name': 'Mathematics', 'avg_pct': 28.0, 'status': 'Weak'},
                {'subject_name': 'Science', 'avg_pct': 37.0, 'status': 'Weak'},
            ]
            risk_info = {'available': True, 'label': 'High', 'proba': 0.85}
            
            pdf_buffer = create_student_performance_pdf(student, subject_stats, risk_info)
            print(f"✓ Student PDF generated successfully ({len(pdf_buffer.getvalue())} bytes)")
        else:
            print("⚠ Student not found")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 2: Class Report PDF
    print("\nTest 2: Class Teacher PDF")
    print("-" * 70)
    try:
        from students.models import SchoolClass
        school_class = SchoolClass.objects.first()
        if school_class:
            students = school_class.students.all()[:5]
            rows = []
            for s in students:
                pred = predict_student_risk(s)
                if pred:
                    rows.append({
                        'student': s,
                        'risk_label': 'High' if pred['risk_label'] == 1 else 'Low',
                        'risk_proba': pred['risk_proba']
                    })
            
            pdf_buffer = create_class_report_pdf(school_class, rows)
            print(f"✓ Class PDF generated successfully ({len(pdf_buffer.getvalue())} bytes)")
        else:
            print("⚠ Class not found")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test 3: Management Report PDF
    print("\nTest 3: Management Dashboard PDF")
    print("-" * 70)
    try:
        students = Student.objects.all()[:10]
        rows = []
        for s in students:
            pred = predict_student_risk(s)
            if pred:
                rows.append({
                    'student': s,
                    'risk_label': 'High' if pred['risk_label'] == 1 else 'Low',
                    'risk_proba': pred['risk_proba']
                })
        
        pdf_buffer = create_management_report_pdf(rows)
        print(f"✓ Management PDF generated successfully ({len(pdf_buffer.getvalue())} bytes)")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print("✓ All PDF generation tests completed!")
    print("=" * 70)
    print("\nTo test in browser:")
    print("  1. Login as student: gv10_01 / Password123")
    print("  2. Visit: http://127.0.0.1:8000/analytics/student/export-pdf/")
    print("  3. PDF should download automatically")
    print("\nAdmin access:")
    print("  Visit: http://127.0.0.1:8000/admin/")
    print("  Login with superuser credentials to manage data")

if __name__ == "__main__":
    test_pdf_generation()
