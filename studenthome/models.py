from django.db import models

class Call(models.Model):
    call_choices = ('ABSENT', 'PRESENT')
    created_on = models.DateTimeField(primary_key=True,auto_now_add=True)
    rollno =  models.CharField(max_length=10)
    status = models.CharField(max_length=200, default='ABSENT')
    prevCall = models.ForeignKey('self',null=True,on_delete=models.CASCADE)

# Create your models here
class StudentInfo(models.Model):
    CURRENT = ( ('ABSENT', 'Not in class'),
                ('CORRECT', 'Correct'),
                ('WRONG', 'Wrong'))
    name=models.CharField(max_length=100)
    imagePath = models.CharField(max_length=200)
    rollno =  models.CharField(primary_key=True,max_length=10)
    username =  models.CharField(max_length=10,null=True)
    presentCount=models.IntegerField(default=0)
    absentCount = models.IntegerField(default=0)
    awakeCount=models.IntegerField(default=0)
    curr_status = models.CharField(verbose_name='Current status', choices=CURRENT, default='ABSENT', max_length=20 )
    calls=models.ForeignKey(Call,null=True,on_delete=models.CASCADE)

class Question(models.Model):
    q=models.CharField(verbose_name="Question", max_length=1000)
    op1 = models.CharField(verbose_name="Option 1",max_length=500,null=True,blank=True)
    ans1 = models.BooleanField(verbose_name="Option 1 value", default=False)
    op2 = models.CharField(verbose_name="Option 2",max_length=500,null=True,blank=True)
    ans2 = models.BooleanField(verbose_name="Option 2 value", default=False)
    op3 = models.CharField(verbose_name="Option 3",max_length=500,null=True,blank=True)
    ans3 = models.BooleanField(verbose_name="Option 3 value", default=False)
    op4 = models.CharField(verbose_name="Option 4",max_length=500,null=True,blank=True)
    ans4 = models.BooleanField(verbose_name="Option 4 value", default=False)
    op5 = models.CharField(verbose_name="Option 5",max_length=500,null=True,blank=True)
    ans5 = models.BooleanField(verbose_name="Option 5 value", default=False)

class StudentAnswers(models.Model):
    rollno =  models.CharField(max_length=10)
    q = models.IntegerField(verbose_name="Question number",    default=0    )
    answer_time = models.DateTimeField(null=True)
    user_agent = models.CharField(verbose_name='Device Used',  max_length=100,null=True )
    op1 = models.IntegerField(verbose_name="Option number 1",    default=0    )
    op2 = models.IntegerField(verbose_name="Option number 2",    default=0    )
    op3 = models.IntegerField(verbose_name="Option number 3",    default=0    )
    op4 = models.IntegerField(verbose_name="Option number 4",    default=0    )
    ans1 = models.BooleanField(verbose_name="Answer given 1", default=False)
    ans2 = models.BooleanField(verbose_name="Answer given 2", default=False)
    ans3 = models.BooleanField(verbose_name="Answer given 3", default=False)
    ans4 = models.BooleanField(verbose_name="Answer given 4", default=False)

class SystemState(models.Model):
    SYS_MODE = ( ( 'QUIZ', 'Quiz is running'), ('INACTIVE','Inactive') )
    activeq = models.IntegerField(verbose_name="Question number", default=0    )
    num_answered = models.IntegerField(verbose_name="Number of students answered", default=0)
    mode = models.CharField(verbose_name='Mode', choices=SYS_MODE, default='INACTIVE', max_length=20 )
