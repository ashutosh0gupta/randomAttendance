from django.shortcuts import render, get_object_or_404

# Create your views here.
from django.template import loader, RequestContext
from django.http import HttpResponse
from .models import StudentInfo
import csv
import os

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
    context = RequestContext(request)
    context.push( {'student_list': student_list } )
    return render( request, 'studenthome/all.html', context.flatten() )


def db_import(request):
    imported=''
    csv_file = os.path.expanduser('~/downloads/output.csv')
    with open(csv_file) as f:
        reader = csv.reader(f)
        for row in reader:
            _, created = StudentInfo.objects.get_or_create(
                rollno=row[1],
                name=row[2],
                imagePath=row[3],
                )
            # created = True
            if created:
                imported=imported + row[1]+"," + row[2]+","+row[3]+"<br>"

    return HttpResponse(imported)
