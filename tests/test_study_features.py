#!/usr/bin/env python
"""
Test script for Topic Mastery Heatmap and Weekly Study Plan features
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'students_performance.settings')
django.setup()

from students.models import Student
from analytics.topic_mastery_utils import calculate_topic_mastery, build_heatmap_data, get_weak_topics
from analytics.study_plan_utils import generate_weekly_study_plan, get_study_recommendations

def test_features():
    print("=" * 70)
    print("Testing Topic Mastery & Study Plan Features")
    print("=" * 70)
    
    # Get a test student
    try:
        student = Student.objects.filter(user__username='gv10_01').first()
        if not student:
            print("❌ Student 'gv10_01' not found")
            return
        
        print(f"\n✓ Testing with student: {student.user.username}")
        print(f"  Class: {student.school_class}")
        
        # Test 1: Topic Mastery Calculation
        print("\n" + "-" * 70)
        print("Test 1: Topic Mastery Calculation")
        print("-" * 70)
        
        mastery_data = calculate_topic_mastery(student)
        if mastery_data:
            print(f"✓ Calculated mastery for {len(mastery_data)} subjects")
            for subject, topics in mastery_data.items():
                print(f"\n  {subject}:")
                for topic, details in topics.items():
                    level_icon = "🔴" if details['level'] == 'Weak' else "🟡" if details['level'] == 'Average' else "🟢"
                    print(f"    {level_icon} {topic}: {details['mastery_score']:.1f}% ({details['level']})")
        else:
            print("⚠ No mastery data (student may not have assessments with topics)")
        
        # Test 2: Heatmap Data Structure
        print("\n" + "-" * 70)
        print("Test 2: Heatmap Data Structure")
        print("-" * 70)
        
        heatmap_data = build_heatmap_data(student)
        if heatmap_data['subjects']:
            print(f"✓ Heatmap built successfully")
            print(f"  Subjects: {len(heatmap_data['subjects'])}")
            print(f"  Topics: {len(heatmap_data['topics'])}")
            print(f"  Matrix dimensions: {len(heatmap_data['matrix'])} x {len(heatmap_data['matrix'][0]) if heatmap_data['matrix'] else 0}")
        else:
            print("⚠ No heatmap data available")
        
        # Test 3: Weak Topics Identification
        print("\n" + "-" * 70)
        print("Test 3: Weak Topics Identification")
        print("-" * 70)
        
        weak_topics = get_weak_topics(student, threshold=60)
        if weak_topics:
            print(f"✓ Found {len(weak_topics)} weak topics")
            for i, topic in enumerate(weak_topics[:5], 1):
                print(f"  {i}. {topic['subject']} - {topic['topic']}: {topic['score']:.1f}%")
        else:
            print("✓ No weak topics found (student is performing well!)")
        
        # Test 4: Weekly Study Plan Generation
        print("\n" + "-" * 70)
        print("Test 4: Weekly Study Plan Generation")
        print("-" * 70)
        
        study_plan = generate_weekly_study_plan(student)
        if study_plan:
            print(f"✓ Study plan generated successfully")
            print(f"  Week: {study_plan['week_start']} to {study_plan['week_end']}")
            print(f"  Total hours: {study_plan['summary']['total_hours']}")
            print(f"  Weak topics targeted: {study_plan['summary']['weak_topics_count']}")
            print(f"  Subjects covered: {study_plan['summary']['subjects_covered']}")
            
            print("\n  Daily Schedule:")
            for day, tasks in study_plan['daily_schedule'].items():
                if tasks:
                    total_time = sum(t['duration'] for t in tasks)
                    print(f"    {day}: {len(tasks)} tasks ({total_time}h)")
                else:
                    print(f"    {day}: Rest day")
        else:
            print("⚠ No study plan generated")
        
        # Test 5: Study Recommendations
        print("\n" + "-" * 70)
        print("Test 5: Study Recommendations")
        print("-" * 70)
        
        recommendations = get_study_recommendations(student)
        if recommendations:
            print(f"✓ Generated {len(recommendations)} recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print("⚠ No recommendations generated")
        
        print("\n" + "=" * 70)
        print("✓ All tests completed successfully!")
        print("=" * 70)
        print("\nTo view in browser:")
        print("  1. Login as student: gv10_01 / Password123")
        print("  2. Navigate to: http://127.0.0.1:8000/analytics/student/")
        print("  3. Scroll down to see 'Topic Mastery Heatmap' and 'Weekly Study Plan'")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_features()
