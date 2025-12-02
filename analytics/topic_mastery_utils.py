"""
Topic Mastery Utilities
Calculates and structures topic mastery data for heatmap visualization
"""
import numpy as np
from collections import defaultdict
from assessments.models import Assessment


def calculate_topic_mastery(student):
    """
    Calculate mastery scores for each topic the student has been assessed on.
    
    Returns:
        dict: {
            'subject_name': {
                'topic_name': {
                    'mastery_score': float (0-100),
                    'level': str ('Weak'|'Average'|'Strong'),
                    'avg_marks': float,
                    'trend': float,
                    'consistency': float,
                    'assessment_count': int
                }
            }
        }
    """
    assessments = Assessment.objects.filter(student=student).order_by('exam_date')
    
    if not assessments.exists():
        return {}
    
    # Group assessments by subject and topic
    topic_data = defaultdict(lambda: defaultdict(list))
    
    for a in assessments:
        if a.topic:  # Only process if topic is set
            subject_name = a.subject.name
            topic_name = a.topic
            
            # Calculate percentage
            if a.max_marks and float(a.max_marks) > 0:
                pct = (float(a.marks_obtained) / float(a.max_marks)) * 100.0
                topic_data[subject_name][topic_name].append(pct)
    
    # Calculate mastery metrics for each topic
    mastery_results = {}
    
    for subject_name, topics in topic_data.items():
        mastery_results[subject_name] = {}
        
        for topic_name, marks_list in topics.items():
            if not marks_list:
                continue
            
            # Calculate metrics
            avg_marks = float(np.mean(marks_list))
            
            # Trend: improvement over time (compare first half vs second half)
            if len(marks_list) >= 4:
                mid = len(marks_list) // 2
                first_half_avg = np.mean(marks_list[:mid])
                second_half_avg = np.mean(marks_list[mid:])
                trend = (second_half_avg - first_half_avg) / 100.0  # Normalize to 0-1
            else:
                trend = 0.0
            
            # Consistency: inverse of variance (lower variance = higher consistency)
            if len(marks_list) > 1:
                variance = np.var(marks_list)
                # Normalize: high variance (400) = low consistency (0), low variance (0) = high consistency (1)
                consistency = max(0, 1 - (variance / 400.0))
            else:
                consistency = 0.5  # Neutral for single assessment
            
            # Calculate mastery score (weighted combination)
            mastery_score = (avg_marks * 0.6) + (trend * 100 * 0.2) + (consistency * 100 * 0.2)
            mastery_score = max(0, min(100, mastery_score))  # Clamp to 0-100
            
            # Determine level
            level = get_mastery_level(mastery_score)
            
            mastery_results[subject_name][topic_name] = {
                'mastery_score': round(mastery_score, 1),
                'level': level,
                'avg_marks': round(avg_marks, 1),
                'trend': round(trend, 2),
                'consistency': round(consistency, 2),
                'assessment_count': len(marks_list)
            }
    
    return mastery_results


def get_mastery_level(score):
    """Convert mastery score to level category"""
    if score < 50:
        return 'Weak'
    elif score < 70:
        return 'Average'
    else:
        return 'Strong'


def build_heatmap_data(student):
    """
    Build structured data for heatmap visualization.
    
    Returns:
        dict: {
            'subjects': [list of subject names],
            'topics': [list of all unique topics],
            'matrix': [[mastery_scores]], # 2D array: subjects x topics
            'details': {subject: {topic: details_dict}}
        }
    """
    mastery_data = calculate_topic_mastery(student)
    
    if not mastery_data:
        return {
            'subjects': [],
            'topics': [],
            'matrix': [],
            'details': {}
        }
    
    # Collect all unique topics across all subjects
    all_topics = set()
    for subject_topics in mastery_data.values():
        all_topics.update(subject_topics.keys())
    
    subjects = sorted(mastery_data.keys())
    topics = sorted(all_topics)
    
    # Build matrix
    matrix = []
    for subject in subjects:
        row = []
        for topic in topics:
            if topic in mastery_data[subject]:
                row.append(mastery_data[subject][topic]['mastery_score'])
            else:
                row.append(None)  # No data for this subject-topic combination
        matrix.append(row)
    
    return {
        'subjects': subjects,
        'topics': topics,
        'matrix': matrix,
        'details': mastery_data
    }


def get_weak_topics(student, threshold=60):
    """
    Get list of weak topics for the student.
    
    Args:
        student: Student instance
        threshold: Mastery score below which topic is considered weak
    
    Returns:
        list: [{'subject': str, 'topic': str, 'score': float, 'level': str}]
    """
    mastery_data = calculate_topic_mastery(student)
    weak_topics = []
    
    for subject_name, topics in mastery_data.items():
        for topic_name, details in topics.items():
            if details['mastery_score'] < threshold:
                weak_topics.append({
                    'subject': subject_name,
                    'topic': topic_name,
                    'score': details['mastery_score'],
                    'level': details['level'],
                    'avg_marks': details['avg_marks']
                })
    
    # Sort by score (weakest first)
    weak_topics.sort(key=lambda x: x['score'])
    
    return weak_topics
