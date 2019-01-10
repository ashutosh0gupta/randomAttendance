from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.template import loader, RequestContext
from django.http import HttpResponse
from .models import StudentInfo
import csv
import os
import shutil

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

def status(request, rollno):
    student = get_object_or_404(StudentInfo, pk=rollno)
    if request.POST:
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
    count_list = dict()
    absent_count = 0
    present_count = 0
    awake_count = 0    
    for student in student_list:
        called_count = student.absentCount+student.presentCount+student.awakeCount
        absent_count = absent_count + student.absentCount
        present_count = present_count + student.presentCount
        awake_count = awake_count + student.awakeCount        
        if called_count in count_list:
            count_list[called_count] = count_list[called_count] + 1
        else:
            count_list[called_count] = 1
    context = RequestContext(request)
    context.push( {'student_list': student_list, 'count_list': count_list, 'absent_count': absent_count, 'present_count': present_count, 'awake_count': awake_count, 'show_photo' : False, } )
    return render( request, 'studenthome/all.html', context.flatten() )


def db_import(request):
    imported=''
    csv_file = os.path.expanduser('/tmp/output.csv')
    current_rolls = []
    with open(csv_file) as f:
        reader = csv.reader(f)
        for row in reader:
            _, created = StudentInfo.objects.get_or_create(
                rollno=row[1],
                name=row[2],
                imagePath=row[3],
                )
            current_rolls.append( row[1] )
            if created:
                shutil.copy('/tmp/'+row[3],'studenthome/images/'+row[3])
                imported=imported + row[1]+"," + row[2]+","+row[3]+"<br>"
    imported=imported + "To be deleted students: <br>(to avoid accedental deletion, user needs to do it manually goto <home>/admin/)<br>"
    student_list = StudentInfo.objects.order_by('rollno')
    for student in student_list:
        if student.rollno not in current_rolls:
            imported=imported + student.rollno + "<br>"

    return HttpResponse(imported)
