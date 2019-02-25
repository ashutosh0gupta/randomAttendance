from django.db import models

class Call(models.Model):
    call_choices = ('ABSENT', 'PRESENT')
    created_on = models.DateTimeField(primary_key=True,auto_now_add=True)
    rollno =  models.CharField(max_length=10)
    status = models.CharField(max_length=200, default='ABSENT')
    prevCall = models.ForeignKey('self',null=True,on_delete=models.CASCADE)

# Create your models here
class StudentInfo(models.Model):
    name=models.CharField(max_length=100)
    imagePath = models.CharField(max_length=200)
    rollno =  models.CharField(primary_key=True,max_length=10)
    presentCount=models.IntegerField(default=0)
    absentCount = models.IntegerField(default=0)
    awakeCount=models.IntegerField(default=0)
    calls=models.ForeignKey(Call,null=True,on_delete=models.CASCADE)

