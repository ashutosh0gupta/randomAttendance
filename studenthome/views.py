from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.template import loader, RequestContext
from django.http import HttpResponse
from .models import StudentInfo

import random

def index(request):
    student_list = StudentInfo.objects.order_by('rollno')
    if len(student_list) == 0:
        return HttpResponse("No students in the class!!")
    else:
        student = random.choice( student_list )
        context = RequestContext(request)
        context.push( {'student': student, 'getstatus' : True, } )
        return render( request, 'studenthome/index.html', context.flatten() )

def status(request, student_id):
    student = get_object_or_404(StudentInfo, pk=student_id)
    st = request.POST['status']
    if st == 'Absent':
        student.absentCount += 1
    if st == 'Sleepy':
        student.presentCount += 1
    if st == 'Awake':
        student.awakeCount += 1
    student.save()
    context = RequestContext(request)
    context.push( {'student': student, 'getstatus' : False, } )
    return render( request, 'studenthome/index.html', context.flatten() )

def all_status(request):
    student_list = StudentInfo.objects.order_by('rollno')
    context = RequestContext(request)
    context.push( {'student_list': student_list } )
    return render( request, 'studenthome/all.html', context.flatten() )
