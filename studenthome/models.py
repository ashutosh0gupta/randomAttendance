from django.db import models

class Call(models.Model):
    call_choices = ('ABSENT', 'PRESENT')
    created_on   = models.DateTimeField(primary_key=True,auto_now_add=True)
    rollno       = models.CharField(max_length=10)
    status       = models.CharField(max_length=200, default='ABSENT')
    prevCall     = models.ForeignKey('self',null=True,on_delete=models.CASCADE)

# Create your models here
class StudentInfo(models.Model):
    CURRENT = ( ('ABSENT', 'Not in class'),
                ('PART_FINISHED', 'Part Finished'),
                ('CORRECT', 'Correct'),
                ('PART_CORRECT', 'Half Correct'),
                ('WRONG', 'Wrong'))    
    # COURSES = ( ('NONE'  , '-----'      ),
    #             ('THEORY', 'CS213'      ),
    #             ('LAB'   , 'CS293'      ),
    #             ('BOTH'  , 'CS293-CS213') )   
    name=models.CharField(max_length=100)
    imagePath   = models.CharField(max_length=200)
    rollno      = models.CharField(primary_key=True,max_length=10)
    username    = models.CharField(max_length=32,null=True)
    presentCount= models.IntegerField(default=0)
    absentCount = models.IntegerField(default=0)
    awakeCount  = models.IntegerField(default=0)
    isPwd       = models.BooleanField(verbose_name="Is PwD?", default=False)
    exam_area   = models.CharField(max_length=32,null=True)
    exam_room   = models.CharField(max_length=32,null=True)
    exam_seat   = models.CharField(max_length=32,null=True)
    # course      = models.CharField(verbose_name='Enrolled Courses', choices=COURSES, default='BOTH', max_length=20)
    course      = models.CharField(verbose_name='Enrolled Courses', default='---', max_length=20)
    curr_status = models.CharField(verbose_name='Current status', choices=CURRENT, default='ABSENT', max_length=20 )

class Question(models.Model):
    q=models.CharField(verbose_name="Question", max_length=1000)
    course = models.CharField(verbose_name="Course",max_length=10,null=True)
    trues=models.TextField(verbose_name="True Options(new line separated)",max_length=3000,null=True)
    falses=models.TextField(verbose_name="False Options (new line separated)",max_length=3000,null=True)
    # fillCode = models.TextField(verbose_name="Filler",max_length=500,null=True,blank=True)
    # checkCode = models.TextField(verbose_name="Checker",max_length=500,null=True,blank=True)
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
    op6 = models.CharField(verbose_name="Option 6",max_length=500,null=True,blank=True)
    ans6 = models.BooleanField(verbose_name="Option 6 value", default=False)
    op7 = models.CharField(verbose_name="Option 7",max_length=500,null=True,blank=True)
    ans7 = models.BooleanField(verbose_name="Option 7 value", default=False)
    op8 = models.CharField(verbose_name="Option 8",max_length=500,null=True,blank=True)
    ans8 = models.BooleanField(verbose_name="Option 8 value", default=False)
    op9 = models.CharField(verbose_name="Option 9",max_length=500,null=True,blank=True)
    ans9 = models.BooleanField(verbose_name="Option 9 value", default=False)
    op10 = models.CharField(verbose_name="Option 10",max_length=500,null=True,blank=True)
    ans10 = models.BooleanField(verbose_name="Option 10 value", default=False)
    op11 = models.CharField(verbose_name="Option 11",max_length=500,null=True,blank=True)
    ans11 = models.BooleanField(verbose_name="Option 11 value", default=False)
    op12 = models.CharField(verbose_name="Option 12",max_length=500,null=True,blank=True)
    ans12 = models.BooleanField(verbose_name="Option 12 value", default=False)
    op13 = models.CharField(verbose_name="Option 13",max_length=500,null=True,blank=True)
    ans13 = models.BooleanField(verbose_name="Option 13 value", default=False)
    op14 = models.CharField(verbose_name="Option 14",max_length=500,null=True,blank=True)
    ans14 = models.BooleanField(verbose_name="Option 14 value", default=False)
    op15 = models.CharField(verbose_name="Option 15",max_length=500,null=True,blank=True)
    ans15 = models.BooleanField(verbose_name="Option 15 value", default=False)
    op16 = models.CharField(verbose_name="Option 16",max_length=500,null=True,blank=True)
    ans16 = models.BooleanField(verbose_name="Option 16 value", default=False)
    op17  = models.CharField(verbose_name="Option 17",max_length=500,null=True,blank=True)
    ans17 = models.BooleanField(verbose_name="Option 17 value", default=False)
    op18 = models.CharField(verbose_name="Option 18",max_length=500,null=True,blank=True)
    ans18 = models.BooleanField(verbose_name="Option 18 value", default=False)
    op19 = models.CharField(verbose_name="Option 19",max_length=500,null=True,blank=True)
    ans19 = models.BooleanField(verbose_name="Option 19 value", default=False)
    op20 = models.CharField(verbose_name="Option 20",max_length=500,null=True,blank=True)
    ans20 = models.BooleanField(verbose_name="Option 20 value", default=False)
    first_activation_time = models.DateTimeField(verbose_name="Activation time", null=True)



class StudentAnswers(models.Model):
    rollno =  models.CharField(max_length=10)
    q = models.IntegerField(verbose_name="Question number",    default=0    )
    answer_time = models.DateTimeField(null=True)
    is_correct = models.BooleanField(verbose_name="Answer status", default=False)
    correct_count = models.IntegerField(verbose_name="Number of currect answers", default=0)
    user_agent = models.CharField(verbose_name='Device Used',  max_length=100,null=True )
    op1 = models.IntegerField ( verbose_name = "Option number 1", default=0    )
    op2 = models.IntegerField ( verbose_name = "Option number 2", default=0    )
    op3 = models.IntegerField ( verbose_name = "Option number 3", default=0    )
    op4 = models.IntegerField ( verbose_name = "Option number 4", default=0    )
    ans1 = models.BooleanField( verbose_name = "Answer given 1" , default=False)
    ans2 = models.BooleanField( verbose_name = "Answer given 2" , default=False)
    ans3 = models.BooleanField( verbose_name = "Answer given 3" , default=False)
    ans4 = models.BooleanField( verbose_name = "Answer given 4" , default=False)


class BioBreak(models.Model):
    rollno = models.CharField(max_length=10)
    area   = models.CharField(max_length=50,default="",null=True)
    room   = models.CharField(max_length=50,default="",null=True)
    seat   = models.CharField(max_length=50,default="",null=True)
    imagePath     = models.CharField(max_length=200,default="")
    request_time  = models.DateTimeField(null=True)
    activate_time = models.DateTimeField(null=True)
    returned_time = models.DateTimeField(null=True)
    out_time      = models.IntegerField ( verbose_name = "Out time", default=0    )

#---------------------------------------------------------
# Exam rooms
#---------------------------------------------------------

class ExamRoom(models.Model):
    name = models.CharField(max_length=10)
    area = models.CharField(max_length=50,default="",null=True)
    seats= models.TextField(verbose_name="Available seats(new line separated)",max_length=3000,null=True)
    available = models.BooleanField( verbose_name = "Room Available" , default=True)
    capacity = models.IntegerField( verbose_name="Capacity", default=0    )

#---------------------------------------------------------
# Exam interface
#---------------------------------------------------------
#
# Add exam
# Delete exam
# Edit exam
# Upload student scores
# Edit student scores
# Upload crib scores
#--------------------------------------------------------

class ExamMark(models.Model):
    rollno      = models.CharField(max_length=10)
    exam        = models.CharField(max_length=10)
    q           = models.IntegerField( verbose_name="Question Number", default=0    )
    mark        = models.IntegerField(verbose_name="Marks", default=0 )
    crib        = models.IntegerField(verbose_name="Final Marks",null=True )
    comment     = models.TextField(verbose_name="Comments",max_length=200,null=True)

class Crib(models.Model):
    rollno        = models.CharField(max_length=10)
    exam          = models.CharField(max_length=10)
    q             = models.IntegerField( verbose_name="Question Number", default=0    )
    claim         = models.TextField(verbose_name="Comment",max_length=200,null=True)
    comment       = models.TextField(verbose_name="Comments",max_length=200,null=True)
    raise_time    = models.DateTimeField(null=True)
    is_accepted   = models.BooleanField( verbose_name = "Is crib accepted?" , default=False)
    response_time = models.DateTimeField(null=True)
    mark          = models.IntegerField(verbose_name="Crib Marks",null=True )
    ta            = models.CharField(max_length=20)

class Exam(models.Model):
    name   = models.CharField   ( max_length=10 )
    course = models.CharField   ( max_length=10, default="")
    weight = models.IntegerField ( verbose_name = "Weight of the exam", default=0  )
    total  = models.IntegerField( verbose_name="Total", default=0    )
    num_q  = models.IntegerField ( verbose_name="Number of questions", default=0    )
    mark1  = models.IntegerField ( verbose_name = "Marks Question 1", null=True, blank=True )
    mark2  = models.IntegerField ( verbose_name = "Marks Question 2", null=True, blank=True )
    mark3  = models.IntegerField ( verbose_name = "Marks Question 3", null=True, blank=True )
    mark4  = models.IntegerField ( verbose_name = "Marks Question 4", null=True, blank=True )
    mark5  = models.IntegerField ( verbose_name = "Marks Question 5", null=True, blank=True )
    mark6  = models.IntegerField ( verbose_name = "Marks Question 6", null=True, blank=True )
    mark7  = models.IntegerField ( verbose_name = "Marks Question 7", null=True, blank=True )
    mark8  = models.IntegerField ( verbose_name = "Marks Question 8", null=True, blank=True )
    mark9  = models.IntegerField ( verbose_name = "Marks Question 9", null=True, blank=True )
    mark10 = models.IntegerField ( verbose_name = "Marks Question 10", null=True, blank=True )
    marks  = models.TextField( verbose_name="Student scorse in (CSV) (Header: Roll No,q1,q2,..,qk)", max_length=3000, null=True, blank=True)
    is_cribs_active = models.BooleanField( verbose_name = "Is Cribs active?" , default=True)
    

#---------------------------------------------------------
# Overall system
#---------------------------------------------------------
    
class SystemState(models.Model):
    SYS_MODE = ( ( 'QUIZ', 'Quiz is running'), ('INACTIVE','Inactive') )
    activeq1 = models.IntegerField(verbose_name="Quiz Question 1", default=0    )
    activeq2 = models.IntegerField(verbose_name="Quiz Question 2", default=0    )
    activeq3 = models.IntegerField(verbose_name="Quiz Question 3", default=0    )
    activeq4 = models.IntegerField(verbose_name="Quiz Question 4", default=0    )
    num_answered = models.IntegerField(verbose_name="Number of students answered", default=0)
    num_attendance = models.IntegerField(verbose_name="Number of attendance", default=0)
    mode = models.CharField(verbose_name='Mode', choices=SYS_MODE, default='INACTIVE', max_length=20 )
