from django.contrib import admin

# Register your models here.
from .models import StudentInfo,Call,Question,StudentAnswers,SystemState,BioBreak,ExamRoom

admin.site.register(StudentInfo)
admin.site.register(Call)
admin.site.register(Question)
admin.site.register(StudentAnswers)
admin.site.register(SystemState)
admin.site.register(BioBreak)
admin.site.register(ExamRoom)

