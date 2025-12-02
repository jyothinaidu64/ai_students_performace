from rest_framework import serializers
from .models import Subject, Assessment


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'


class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = '__all__'
    
    def validate(self, data):
        """Validate assessment data"""
        # Ensure marks_obtained <= max_marks
        if data.get('marks_obtained') and data.get('max_marks'):
            if data['marks_obtained'] > data['max_marks']:
                raise serializers.ValidationError({
                    'marks_obtained': 'Marks obtained cannot exceed maximum marks.'
                })
        
        # Ensure max_marks > 0
        if data.get('max_marks') and data['max_marks'] <= 0:
            raise serializers.ValidationError({
                'max_marks': 'Maximum marks must be greater than zero.'
            })
        
        # Ensure attendance_percent is between 0 and 100
        if data.get('attendance_percent') is not None:
            if not (0 <= data['attendance_percent'] <= 100):
                raise serializers.ValidationError({
                    'attendance_percent': 'Attendance must be between 0 and 100.'
                })
        
        return data
