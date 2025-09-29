from django.db import models

# Create your models here.

class Author(models.Model): # 저자테이블
    name = models.CharField(max_length=100)
    birth_date = models.DateField(null=True, blank=True)
    def __str__(self):
        return self.name # 관리화면에서저자의이름을표시
    
class Book(models.Model):# 책테이블
    title=models.CharField(max_length=200)
    author=models.ForeignKey(Author, on_delete=models.CASCADE)
    published_date=models.DateField()
    isbn=models.CharField(max_length=13, unique=True)
    def __str__(self):
        return self.title # 관리화면에서책의제목을표시하기위한문자열
    
class Student(models.Model): # 학생테이블
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    student_id = models.CharField(max_length=20, unique=True)

    # objectwise fuction
    def __str__(self):
        return f'{self.name} ({self.student_id})'
    

    # tablewise function / classwise
    @classmethod
    def get_table():
        return Student.objects.all()
    

    # utility function
    @staticmethod
    def anonymous(self):
        return 
