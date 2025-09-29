from django import forms
from .models import Student

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['name', 'department', 'student_id']
        '''widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Full Name',
            'department': 'Department',
            'student_id': 'Student ID',
        }
        help_texts = {
            'student_id': 'Enter a unique student ID.',
        }
        error_messages = {
            'student_id': {
                'unique': "This student ID is already in use.",
            },
        } '''
