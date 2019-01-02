from django.db import models

# Create your models here
class StudentInfo(models.Model):
    name=models.CharField(max_length=100)
    imagePath = models.CharField(max_length=200)
    rollno =  models.CharField(max_length=10)
    presentCount=models.IntegerField(default=0)
    absentCount = models.IntegerField(default=0)
    awakeCount=models.IntegerField(default=0)


