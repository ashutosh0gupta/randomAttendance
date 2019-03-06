from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from django.template import loader, RequestContext
from django.http import HttpResponse
from .models import StudentInfo,Call

import csv
import os
import shutil
import datetime
import random

#----------------------------------------------------------------------------
# utils
def find_never_called(student_list):
    for student in student_list:
        called_count = student.absentCount+student.presentCount
        if called_count == 0:
            return student
    return None

def get_or_none(model, *args, **kwargs):
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        return None

def get_call_list( student ):
    call_list = []
    calls = student.calls
    while calls != None:
        call_list.append(calls)
        calls = calls.prevCall
    return call_list

def is_called_today( student ):
    if student.calls == None:
        return False
    last_call = student.calls.created_on
    if last_call.date() == datetime.date.today():
        return True

def pick_a_student(student_list):
    # do not accept a student that is alreay called today
    already_called_today = True
    today_retry = 0 
    while already_called_today and today_retry < 5:
        # choose a random student
        student = random.choice( student_list )
        if student.presentCount + student.absentCount > 1:
            # retry one time if the student has at least two calls
            r_count = 0
            while random.random() > 0.3 and r_count < 1:
                # retry with 0.7 probability
                studentp = random.choice( student_list )
                if studentp.presentCount + studentp.absentCount < 2:
                    # retry student has less than two calls,switch student
                    student = studentp
                    break
                r_count += 1
        already_called_today = is_called_today( student )
        today_retry  += 1
    return student

#----------------------------------------------------------------------------
# VIEWS

# view to see a random student
def index(request):
    student_list = StudentInfo.objects.order_by('rollno')
    if len(student_list) == 0:
        return HttpResponse("No students in the class!!")
    else:
        student = pick_a_student( student_list )
        context = RequestContext(request)
        context.push( {'student': student, 'getstatus' : True, } )
        return render( request, 'studenthome/index.html', context.flatten() )

# view to find a student that was never called
def never(request):
    student_list = StudentInfo.objects.order_by('rollno')
    if len(student_list) == 0:
        return HttpResponse("No students in the class!!")
    else:
        student = find_never_called( student_list )
        context = RequestContext(request)
        context.push( {'student': student, 'getstatus' : True, 'ata': True} )
        return render( request, 'studenthome/index.html', context.flatten() )

# view to look or modify student data
def status(request, rollno):
    # student = get_object_or_404(StudentInfo, pk=rollno)
    student = get_or_none(StudentInfo, pk=rollno)
    if student == None:
        return HttpResponse( "No student for roll number : " + str(rollno) )        
    if request.POST:
        st = request.POST['status']
        if st == 'Absent' or st == 'Present':
            if st == 'Absent':
                student.absentCount += 1
            elif st == 'Present':
                student.presentCount += 1
            student.calls = Call.objects.create(
                rollno=student.rollno,
                status=st,
                prevCall=student.calls)
            student.save()
        elif st == 'Delete' or st == 'Flip Attendance':
            time = request.POST['event']
            c = student.calls
            i = 0
            next_call = None
            while c != None:
                if c.created_on.isoformat() == time:
                    break
                i = i + 1
                next_call = c
                c = c.prevCall
            if c != None:
                if st == 'Flip Attendance':
                    if c.status == 'Absent':
                        c.status = 'Present'
                        student.absentCount += -1
                        student.presentCount += 1
                    elif c.status == 'Present':
                        c.status = 'Absent'
                        student.absentCount += 1
                        student.presentCount += -1
                    c.save()
                elif st == 'Delete':
                    if c.status == 'Absent':
                        student.absentCount += -1
                    elif c.status == 'Present':
                        student.presentCount += -1                      
                    if i == 0:
                        student.calls = c.prevCall
                    else:
                        next_call.prevCall = c.prevCall
                        next_call.save()
                    c.prevCall = None
                    c.delete()
                student.save()
            else:
                return HttpResponse("no call found for time " + time)
        if st == 'Remove student':
            student_calls = get_call_list( student )
            for c in reversed(student_calls):
                c.delete()
            student.calls = None
            student.save()
            student.delete()
            return HttpResponse( "Student for roll number " + str(rollno) + " has been removed." )
        return redirect( "/"+str(student.rollno)+"/" )
    else:
        call_list = get_call_list( student )
        context = RequestContext(request)
        context.push( {'student': student, 'getstatus' : False, 'call_list' : call_list } )
        return render( request, 'studenthome/index.html', context.flatten() )

# view for status for all the students
def all_status(request):
    student_list = StudentInfo.objects.order_by('rollno')
    count_list = dict()
    absent_count = 0
    present_count = 0    
    max_called_count = 0
    print_calls = dict()
    for student in student_list:
        called_count = student.absentCount+student.presentCount
        absent_count = absent_count + student.absentCount
        present_count = present_count + student.presentCount        
        if called_count in count_list:
            count_list[called_count] = count_list[called_count] + 1
        else:
            count_list[called_count] = 1
        if called_count > max_called_count:
            max_called_count = called_count
        call_list = get_call_list( student )
        print_calls[student.rollno] = call_list
    called_idxs = []
    called_counts = []    
    for called_count in range(max_called_count+1):
        called_idxs.append( called_count )
        if called_count in count_list:
            called_counts.append( count_list[called_count] )
        else:
            called_counts.append( 0 )
    context = RequestContext(request)
    context.push( {'student_list': student_list, 'called_idxs': called_idxs, 'called_counts': called_counts, 'absent_count': absent_count, 'present_count': present_count, 'print_calls' : print_calls, 'show_photo' : False, } )
    return render( request, 'studenthome/all.html', context.flatten() )


# view for loading student list from ASC website
def db_import(request):
    imported=''
    csv_file = os.path.expanduser('/tmp/output.csv')
    current_rolls = []
    try:
        with open(csv_file) as f:
            reader = csv.reader(f)
            for row in reader:
                student, created = StudentInfo.objects.get_or_create(
                    rollno=row[1]
                )
                current_rolls.append( row[1] )
                if created:
                    student.name = row[2]
                    student.imagePath = row[3]
                    student.calls = None
                    student.save()
                    shutil.copy('/tmp/'+row[3],'studenthome/images/'+row[3])
                    imported += row[1]+"," + row[2]+","+row[3]+"<br>"
    except IOError as e:
        return HttpResponse( "Failed to open file "+csv_file + ".<br> Look into README for importing students!")
    deleted  = "The following students are not in rolls any more."
    deleted += "to be deleted students:<br>"
    deleted += "(To avoid accedental deletion, user needs to do it manually."
    deleted += "goto to the student page)<br>"
    student_list = StudentInfo.objects.order_by('rollno')
    any_deleted = False
    for student in student_list:
        if student.rollno not in current_rolls:
            deleted += "<a href=\"/" + student.rollno + "\">" + student.rollno + "</a><br>"
            any_deleted = True
    if not any_deleted:
        deleted = ''
    return HttpResponse(imported+deleted)
