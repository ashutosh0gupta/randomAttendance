from django.contrib import admin

# Register your models here.
from .models import StudentInfo,Call,Question,StudentAnswers,SystemState,BioBreak,Exam,ExamRoom,ExamMark

admin.site.register(StudentInfo)
admin.site.register(Call)
admin.site.register(Question)
admin.site.register(StudentAnswers)
admin.site.register(SystemState)
admin.site.register(BioBreak)
admin.site.register(Exam)
admin.site.register(ExamRoom)
admin.site.register(ExamMark)

