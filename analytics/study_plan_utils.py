"""
Weekly Study Plan Generator
Rule-based algorithm to generate personalized study schedules
"""
from datetime import datetime, timedelta
from collections import defaultdict
from .topic_mastery_utils import get_weak_topics, calculate_topic_mastery


def generate_weekly_study_plan(student):
    """
    Generate a personalized weekly study plan for the student.
    
    Returns:
        dict: {
            'week_start': date,
            'week_end': date,
            'daily_schedule': {
                'Monday': [tasks],
                'Tuesday': [tasks],
                ...
            },
            'summary': {
                'total_hours': float,
                'weak_topics_count': int,
                'subjects_covered': int
            }
        }
    """
    # Get weak topics
    weak_topics = get_weak_topics(student, threshold=60)
    
    # Get all topic mastery data
    mastery_data = calculate_topic_mastery(student)
    
    # Identify topics to focus on
    focus_topics = identify_focus_topics(weak_topics, mastery_data)
    
    # Calculate time allocation
    time_allocation = calculate_study_time_allocation(focus_topics)
    
    # Create daily schedule
    daily_schedule = create_daily_schedule(time_allocation)
    
    # Calculate week dates
    today = datetime.now().date()
    # Start from next Monday
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7  # If today is Monday, start next Monday
    week_start = today + timedelta(days=days_until_monday)
    week_end = week_start + timedelta(days=6)
    
    # Calculate summary
    total_hours = sum(task['duration'] for day_tasks in daily_schedule.values() for task in day_tasks)
    subjects_covered = len(set(task['subject'] for day_tasks in daily_schedule.values() for task in day_tasks))
    
    return {
        'week_start': week_start,
        'week_end': week_end,
        'daily_schedule': daily_schedule,
        'summary': {
            'total_hours': round(total_hours, 1),
            'weak_topics_count': len(weak_topics),
            'subjects_covered': subjects_covered
        }
    }


def identify_focus_topics(weak_topics, mastery_data):
    """
    Identify and prioritize topics to focus on.
    
    Returns:
        list: [
            {
                'subject': str,
                'topic': str,
                'priority': int (1-5, 5 being highest),
                'mastery_score': float,
                'reason': str
            }
        ]
    """
    focus_list = []
    
    # Add weak topics with high priority
    for weak in weak_topics[:10]:  # Limit to top 10 weakest
        priority = 5 if weak['score'] < 40 else 4
        focus_list.append({
            'subject': weak['subject'],
            'topic': weak['topic'],
            'priority': priority,
            'mastery_score': weak['score'],
            'reason': f"Weak topic (score: {weak['score']:.0f}%)"
        })
    
    # Add average topics for balanced learning
    for subject_name, topics in mastery_data.items():
        for topic_name, details in topics.items():
            if 60 <= details['mastery_score'] < 75:
                # Check if not already in focus list
                if not any(f['topic'] == topic_name and f['subject'] == subject_name for f in focus_list):
                    focus_list.append({
                        'subject': subject_name,
                        'topic': topic_name,
                        'priority': 3,
                        'mastery_score': details['mastery_score'],
                        'reason': f"Needs improvement (score: {details['mastery_score']:.0f}%)"
                    })
    
    # Sort by priority (highest first)
    focus_list.sort(key=lambda x: x['priority'], reverse=True)
    
    return focus_list


def calculate_study_time_allocation(focus_topics):
    """
    Allocate study time across topics.
    
    Total weekly time: 7.5 hours (1.5 hours/day × 5 days)
    Distribution:
    - 50% weak topics (priority 4-5)
    - 30% average topics (priority 3)
    - 20% revision/practice
    
    Returns:
        list: [
            {
                'subject': str,
                'topic': str,
                'duration': float (hours),
                'priority': int,
                'activity': str
            }
        ]
    """
    total_weekly_hours = 7.5
    
    # Separate by priority
    high_priority = [t for t in focus_topics if t['priority'] >= 4]
    medium_priority = [t for t in focus_topics if t['priority'] == 3]
    
    allocations = []
    
    # Allocate to high priority (50% of time)
    if high_priority:
        time_per_topic = (total_weekly_hours * 0.5) / len(high_priority)
        for topic in high_priority:
            allocations.append({
                'subject': topic['subject'],
                'topic': topic['topic'],
                'duration': round(time_per_topic, 1),
                'priority': topic['priority'],
                'activity': 'Concept review + Practice problems'
            })
    
    # Allocate to medium priority (30% of time)
    if medium_priority:
        time_per_topic = (total_weekly_hours * 0.3) / len(medium_priority)
        for topic in medium_priority[:5]:  # Limit to 5 topics
            allocations.append({
                'subject': topic['subject'],
                'topic': topic['topic'],
                'duration': round(time_per_topic, 1),
                'priority': topic['priority'],
                'activity': 'Practice problems + Quick review'
            })
    
    # Add revision time (20% of time)
    if allocations:
        revision_time = total_weekly_hours * 0.2
        # Distribute revision across subjects
        subjects = list(set(a['subject'] for a in allocations))
        revision_per_subject = revision_time / len(subjects)
        
        for subject in subjects:
            allocations.append({
                'subject': subject,
                'topic': 'General Revision',
                'duration': round(revision_per_subject, 1),
                'priority': 2,
                'activity': 'Solve previous papers + Revise notes'
            })
    
    return allocations


def create_daily_schedule(time_allocation):
    """
    Distribute allocated time across weekdays.
    
    Returns:
        dict: {
            'Monday': [tasks],
            'Tuesday': [tasks],
            ...
        }
    """
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    daily_schedule = {day: [] for day in days}
    
    if not time_allocation:
        return daily_schedule
    
    # Sort allocations by priority
    sorted_allocations = sorted(time_allocation, key=lambda x: x['priority'], reverse=True)
    
    # Distribute across days (round-robin with priority)
    day_index = 0
    for allocation in sorted_allocations:
        # Split larger tasks across multiple days if needed
        remaining_duration = allocation['duration']
        
        while remaining_duration > 0:
            # Max 1.5 hours per day
            session_duration = min(remaining_duration, 1.5)
            
            daily_schedule[days[day_index]].append({
                'subject': allocation['subject'],
                'topic': allocation['topic'],
                'duration': session_duration,
                'activity': allocation['activity'],
                'priority': allocation['priority']
            })
            
            remaining_duration -= session_duration
            day_index = (day_index + 1) % len(days)
    
    # Balance days (ensure no day exceeds 1.5 hours)
    for day in days:
        total_day_time = sum(task['duration'] for task in daily_schedule[day])
        if total_day_time > 1.5:
            # Redistribute excess
            excess = total_day_time - 1.5
            # Remove or reduce lowest priority tasks
            daily_schedule[day].sort(key=lambda x: x['priority'])
            while excess > 0 and daily_schedule[day]:
                task = daily_schedule[day][0]
                if task['duration'] <= excess:
                    excess -= task['duration']
                    daily_schedule[day].pop(0)
                else:
                    task['duration'] -= excess
                    excess = 0
    
    return daily_schedule


def get_study_recommendations(student):
    """
    Get personalized study recommendations based on performance.
    
    Returns:
        list: [str] - List of recommendation strings
    """
    weak_topics = get_weak_topics(student, threshold=60)
    mastery_data = calculate_topic_mastery(student)
    
    recommendations = []
    
    if weak_topics:
        # Identify most critical subject
        subject_weakness = defaultdict(list)
        for topic in weak_topics:
            subject_weakness[topic['subject']].append(topic)
        
        weakest_subject = max(subject_weakness.items(), key=lambda x: len(x[1]))[0]
        weak_count = len(subject_weakness[weakest_subject])
        
        recommendations.append(
            f"Focus on {weakest_subject}: You have {weak_count} weak topics that need immediate attention."
        )
        
        # Specific topic recommendations
        top_3_weak = weak_topics[:3]
        for topic in top_3_weak:
            recommendations.append(
                f"Practice {topic['topic']} in {topic['subject']} - Current score: {topic['score']:.0f}%"
            )
    else:
        recommendations.append("Great job! You're performing well across all topics. Focus on maintaining consistency.")
    
    # Time management recommendation
    recommendations.append("Dedicate 60-90 minutes daily for focused study sessions.")
    
    # Revision recommendation
    recommendations.append("Review your notes within 24 hours of each class for better retention.")
    
    return recommendations[:5]  # Limit to 5 recommendations
