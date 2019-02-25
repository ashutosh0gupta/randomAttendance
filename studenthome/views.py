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

def find_never_called(student_list):
    for student in student_list:
        called_count = student.absentCount+student.presentCount+student.awakeCount
        if called_count == 0:
            return student
    return None

def ata(request):
    student_list = StudentInfo.objects.order_by('rollno')
    if len(student_list) == 0:
        return HttpResponse("No students in the class!!")
    else:
        student = find_never_called( student_list )
        context = RequestContext(request)
        context.push( {'student': student, 'getstatus' : True, 'ata': True} )
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
    max_called_count = 0
    for student in student_list:
        called_count = student.absentCount+student.presentCount+student.awakeCount
        absent_count = absent_count + student.absentCount
        present_count = present_count + student.presentCount
        awake_count = awake_count + student.awakeCount        
        if called_count in count_list:
            count_list[called_count] = count_list[called_count] + 1
        else:
            count_list[called_count] = 1
        if called_count > max_called_count:
            max_called_count = called_count
    called_idxs = []
    called_counts = []    
    for called_count in range(max_called_count+1):
        called_idxs.append( called_count )
        if called_count in count_list:
            called_counts.append( count_list[called_count] )
        else:
            called_counts.append( 0 )
    context = RequestContext(request)
    # context.push( {'student_list': student_list, 'count_list': count_list, 'absent_count': absent_count, 'present_count': present_count, 'awake_count': awake_count, 'show_photo' : False, } )
    context.push( {'student_list': student_list, 'called_idxs': called_idxs, 'called_counts': called_counts, 'absent_count': absent_count, 'present_count': present_count, 'awake_count': awake_count, 'show_photo' : False, } )
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
    deleted="To be deleted students:<br>"
    deleted= deleted+"(to avoid accedental deletion, user needs to do it manually. goto <a href=\"admin/\">admin</a>)<br>"
    student_list = StudentInfo.objects.order_by('rollno')
    any_deleted = False
    for student in student_list:
        if student.rollno not in current_rolls:
            deleted=deleted + student.rollno + "<br>"
            any_deleted = True
    if not any_deleted:
        deleted = ''
    return HttpResponse(imported+deleted)
