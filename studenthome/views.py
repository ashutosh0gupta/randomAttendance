from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from django.template import loader, RequestContext
from django.http import HttpResponse
from .models import StudentInfo,Call,Question,StudentAnswers,SystemState
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin, AccessMixin,UserPassesTestMixin
from django.views.generic.edit import CreateView, DeleteView, UpdateView,FormView
from django.urls import reverse, reverse_lazy
from django.contrib import messages

import csv
import os
import shutil
import datetime
import random
import pylatexenc
from pylatexenc.latex2text import LatexNodes2Text

#----------------------------------------------------------------------------
# utils

# @register.filter
# def hash(h, key):
#     return h[key]

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

# def pick_a_student(student_list):
#     # do not accept a student that is alreay called today
#     already_called_today = True
#     today_retry = 0 
#     while already_called_today and today_retry < 5:
#         # choose a random student
#         student = random.choice( student_list )
#         if student.presentCount + student.absentCount > 1:
#             # retry one time if the student has at least two calls
#             r_count = 0
#             while random.random() > 0.3 and r_count < 1:
#                 # retry with 0.7 probability
#                 studentp = random.choice( student_list )
#                 if studentp.presentCount + studentp.absentCount < 2:
#                     # retry student has less than two calls,switch student
#                     student = studentp
#                     break
#                 r_count += 1
#         already_called_today = is_called_today( student )
#         today_retry  += 1
#     return student

def pick_a_student(student_list):
    return random.choice( student_list )
    
#----------------------------------------------------------------------------
# VIEWS

# def login(request):
#     return HttpResponse("Not implemented yet!!")

# def logout(request):
#     return redirect( reverse("login") )

def get_user_rollno( u ):
    if( u.ldap_user ):
        rollno = u.ldap_user.attrs['employeeNumber']
        return rollno
    else:
        # test situation where we do not care of ldap authenticaiton
        u.username
    # return "150020094"

def who_auth(request):
    u = request.user
    if u.is_anonymous:
        return None
    if u.username == "akg":
        return "prof"
    s = get_or_none( StudentInfo, username = u.username )
    if s == None:
        rollno = get_user_rollno( u )
        assert( len(rollno) > 0 )
        s = get_or_none( StudentInfo, pk = rollno[0] )
        if s == None:
            return None
        else:
            s.username = u.username
            s.save()
            return s.rollno
    else:
        return s.rollno

def get_q_op( q, idx ):
    op = q._meta.get_field("op"+str(idx))
    op_str = op.value_from_object( q )
    if op_str :
        return LatexNodes2Text().latex_to_text( op_str )
    else:
        # assert( False )
        return None

def get_q_ans( q, idx ):
    op = q._meta.get_field("ans"+str(idx))
    return op.value_from_object( q )

    
def get_active_options( q ):
    active_idxes = []
    for i in range(1,21):
        op = q._meta.get_field("op"+str(i))
        op_str = op.value_from_object( q )
        if op_str :
            active_idxes.append( i )
    return active_idxes

def is_answer_correct( sa ):
    q = get_or_none( Question, pk=sa.q )
    s = get_or_none( StudentInfo, pk=sa.rollno )
    result = True
    for idx in range(1,5):
        op = sa._meta.get_field("op"+str(idx))
        op_num = op.value_from_object( sa )
        correct_ans = get_q_ans(q,op_num)
        ans = sa._meta.get_field("ans"+str(idx))
        student_ans = ans.value_from_object( sa )
        if correct_ans != student_ans :
            result = False
            break
    return result

def index(request):
    p = who_auth(request)
    if p == None:
        return redirect( reverse("logout") )
    context = RequestContext(request)
    s = get_sys_state()
    context["sys"] = s
    if p == "prof":
        if s.mode == "QUIZ":
            q = get_or_none( Question, pk=s.activeq )
            context["q"] = LatexNodes2Text().latex_to_text( q.q )
            context[ "students" ] = StudentInfo.objects.all()
            return render( request, 'studenthome/quiz.html', context.flatten() )
        else:
            return render( request, 'studenthome/dashboard.html', context.flatten() )
    # student is logged in
    if s.mode == "QUIZ":
        # q = get_or_none( Question, pk=s.activeq )
        sa = get_or_none( StudentAnswers, rollno=p, q=s.activeq )
        if sa == None:
            return HttpResponse( "Something is wrong!!" )
        return redirect( reverse('answer', kwargs={'ansid':sa.pk}) )
    else:
        return HttpResponse( "Quiz is not running!! Refresh to check if it is running now!" )
    


# view for loading student list from ASC website
def db_import(request):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )

    imported=''
    csv_file = os.path.expanduser('/tmp/output.csv')
    current_rolls = []
    os.makedirs('studenthome/images/', exist_ok=True)
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
                print( "processed: " + row[1] )
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

# view for loading student list from ASC website
    
def question(request):
    if is_student(request):
        return student_attempt(attempt)
    if is_prof(request):
        return show_question(attempt)
    return HttpResponse( 'No login or unregistered user!' )        

q_fields = ['q']
op_fields = []
ans_fields = []
for i in range(1,21):
    q_fields.append('op'+str(i))
    q_fields.append('ans'+str(i))
    op_fields.append('op'+str(i))
    ans_fields.append('ans'+str(i))

class CreateQuestion(SuccessMessageMixin,CreateView):
    model = Question
    fields= q_fields
    template_name = 'studenthome/qcreate.html'

    def get_context_data( self, **kwargs ):
        context = super(CreateQuestion,self).get_context_data(**kwargs)
        context[ "is_auth" ] = (who_auth( self.request ) == "prof")
        context[ "qs" ] = Question.objects.all()
        context[ "sys" ] = get_sys_state()
        return context
    
    def get_success_url(self):
        return reverse( "createq" )

    def form_valid(self,form):
        try:
            d = None
            u = who_auth(self.request)
            if u == None:
                return redirect( reverse("logout") )
            if u != 'prof':
                raise Exception( "Wrong kind of login!" )
            # if not self.request.user.is_authenticated:
            #     raise Exception( "Not logged in!" )
            response = super().form_valid(form)
            d = self.object
            for op_name in op_fields:
                op = d._meta.get_field(op_name)
                op_str = op.value_from_object(d)
                if op_str :
                    uni_op = LatexNodes2Text().latex_to_text(op_str)
                    print(uni_op)
            messages.success(self.request,'Created question '+str(d.id)+'!')

            # bulk create for student resonses
            ops = get_active_options( d )
            sas = []
            for s in StudentInfo.objects.all():
                op = random.sample( ops, 4 )
                sas.append( StudentAnswers(rollno=s.rollno, q=d.pk,
                                           op1 = op[0], op2 = op[1],
                                           op3 = op[2],op4 = op[3] ) )
            StudentAnswers.objects.bulk_create( sas )

            return response
        except Exception as e:
            # Form has failed fill gain
            form.add_error( None, '{}!'.format(e) )
            if d:
                d.delete()
            return super().form_invalid(form)


class EditQuestion(UpdateView):
    model = Question
    fields = q_fields
    template_name = 'studenthome/editq.html'
    pk_url_kwarg = 'qid'
    
    def get_context_data( self, **kwargs ):
        context = super(EditQuestion,self).get_context_data(**kwargs)
        context[ "is_auth" ] = (who_auth( self.request ) == "prof")
        return context

    def get_success_url(self):
        return reverse( "createq" )

def deleteq(request, qid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    q = get_or_none( Question, pk = int(qid) )
    if q:
        messages.success(request,'Question '+str(q.id)+' deleted!')
        q.delete()
    # return HttpResponse( 'Done!' )
    return redirect( reverse( 'createq' ) )

def viewq(request, qid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    q = get_or_none( Question, pk = int(qid) )
    ops = dict()
    for i in range(1,21):
        ops['op'+str(i)] = get_q_op( q, i )
    context = RequestContext(request)
    context.push( {'q': q } )
    context.push( ops )
    return render( request, 'studenthome/viewq.html', context.flatten() )

    
def get_sys_state():
    s, created = SystemState.objects.get_or_create(pk = 1)
    return s

def activateq(request, qid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )

    #update system state
    s = get_sys_state()
    s.activeq = qid
    s.save()

    return redirect( reverse( 'createq' ) )



def startq(request):
    sys = get_sys_state()
    if sys.mode == 'QUIZ':
        return redirect( reverse( 'index' ) )
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    q = get_or_none( Question, pk=sys.activeq )
    ops = get_active_options( q )

    if q.first_activation_time == None:
        StudentInfo.objects.update( curr_status = 'ABSENT')
        
    ss = StudentInfo.objects.all()   
    for s in ss:
        sa = get_or_none( StudentAnswers, rollno=s.rollno, q=sys.activeq )
        if sa == None:
            op = random.sample( ops, 4 )
            sa = StudentAnswers.objects.create(rollno=s.rollno, q=q.pk)
            sa.op1 = op[0]
            sa.op2 = op[1]
            sa.op3 = op[2]
            sa.op4 = op[3]
            sa.save()
        if sa.answer_time == None:
            if s.curr_status != 'ABSENT':
                s.curr_status = 'ABSENT'
                s.save()
        elif is_answer_correct( sa ):
            if s.curr_status != 'CORRECT':
                s.curr_status = 'CORRECT'
                s.save()
        else:
            if s.curr_status != 'WRONG':
                s.curr_status = 'WRONG'
                s.save()
        # print( "start "+ str( datetime.datetime.now() ) )
        # s.save()
        # print( "end "+ str( datetime.datetime.now() ) )
    if q.first_activation_time == None:
        q.first_activation_time = datetime.datetime.now()
        q.save()
        sys.num_attendance = sys.num_attendance + 1
    sys.mode = 'QUIZ'
    sys.save()
    return redirect( reverse( 'index' ) )

def stopq(request):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    sys = get_sys_state()
    if sys.mode == 'INACTIVE':
        return redirect( reverse( 'index' ) )
    sys.mode = 'INACTIVE'
    sys.save()
    # choose three random students that have answered
    student_list = StudentInfo.objects.exclude( curr_status = 'ABSENT' ).all()
    s1 = None
    s2 = None
    s3 = None
    if len(student_list) > 3:
        s1,s2,s3 = random.sample( student_list, 3 )
    else:
        if len(student_list) > 2:
            s3 = student_list[2]
        if len(student_list) > 1:
            s2 = student_list[1]            
        if len(student_list) > 0:
            s1 = student_list[0]
    context = RequestContext(request)
    context.push( {'s1': s1, 's2': s2, 's3': s3 } )
    return render( request, 'studenthome/results.html', context.flatten() )

class StudentResponse(UpdateView):
    model = StudentAnswers
    fields = ['ans1','ans2','ans3','ans4']
    template_name = 'studenthome/answer.html'
    pk_url_kwarg = 'ansid'
    
    def get_context_data( self, **kwargs ):
        context = super(StudentResponse,self).get_context_data(**kwargs)
        sa = self.object
        sys = get_sys_state()
        if sa.answer_time :
            context[ "yet_to_answer" ] = False
        else:
            context[ "yet_to_answer" ] = (sys.mode == 'QUIZ')
        context[ "is_auth" ] = ( who_auth( self.request ) == sa.rollno )
        context[ "sys" ] = sys
        q = get_or_none( Question, pk=sys.activeq )
        # sa = get_or_none( StudentAnswers, ansid )
        # if sa == None:
        #     return HttpResponse( "Something is wrong!!" )            
        context["op1"] = get_q_op( q, sa.op1 )
        context["op2"] = get_q_op( q, sa.op2 )
        context["op3"] = get_q_op( q, sa.op3 )
        context["op4"] = get_q_op( q, sa.op4 )
        context["sa"] = sa
        return context

    def form_valid(self,form):
        try:
            sa = None
            response = super().form_valid(form)
            sa = self.object
            sa.answer_time = datetime.datetime.now()
            sa.user_agent = self.request.headers['User-Agent']
            sa.save()
            s = get_or_none(StudentInfo, pk=sa.rollno)
            if is_answer_correct( sa ):
                s.curr_status = 'CORRECT'
            else:
                s.curr_status = 'WRONG'
            s.presentCount = s.presentCount + 1
            s.save()
            return response
        except Exception as e:
            # Form has failed fill gain
            form.add_error( None, '{}!'.format(e) )
            # messages.error(self.request,'{}!'.format(e))
            return super().form_invalid(form)

    def get_success_url(self):
        return reverse( "index" )



# view for status for all the students
def all_status(request):
    student_list = StudentInfo.objects.order_by('rollno')
    sys = get_sys_state()
    num_attendance = sys.num_attendance
    # count_list = dict()
    absent_count = 0
    present_count = 0    
    # max_called_count = 0
    print_calls = dict()
    for student in student_list:
        # called_count = student.absentCount+student.presentCount
        absent_count = absent_count + num_attendance - student.presentCount
        present_count = present_count +  student.presentCount        
        # if called_count in count_list:
        #     count_list[called_count] = count_list[called_count] + 1
        # else:
        #     count_list[called_count] = 1
        # if called_count > max_called_count:
        #     max_called_count = called_count
        attendances = StudentAnswers.objects.filter( rollno = student.rollno ).exclude(answer_time = None ).all()
        print_calls[student.rollno] = attendances
    # called_idxs = []
    # called_counts = []    
    # for called_count in range(max_called_count+1):
    #     called_idxs.append( called_count )
    #     if called_count in count_list:
    #         called_counts.append( count_list[called_count] )
    #     else:
    #         called_counts.append( 0 )
    context = RequestContext(request)
    context.push( {'student_list': student_list,
                   # 'called_idxs': called_idxs, 'called_counts': called_counts,
                   'absent_count': absent_count, 'present_count': present_count,
                   'print_calls' : print_calls, 'show_photo' : False, } )
    return render( request, 'studenthome/all.html', context.flatten() )

#======================================================
# Old random views

# view to see a random student
def call(request):
    students = StudentInfo.objects.filter( curr_status = 'WRONG' ) | StudentInfo.objects.filter( curr_status = 'CORRECT' )
    student_list = students.all()
    
    if len(student_list) == 0:
        return HttpResponse("No students in the class!!")
    else:
        student = pick_a_student( student_list )
        context = RequestContext(request)
        context.push( {'student': student, 'getstatus' : True, } )
        return render( request, 'studenthome/index.html', context.flatten() )

# # view to find a student that was never called
# def never(request):
#     student_list = StudentInfo.objects.order_by('rollno')
#     if len(student_list) == 0:
#         return HttpResponse("No students in the class!!")
#     else:
#         student = find_never_called( student_list )
#         context = RequestContext(request)
#         context.push( {'student': student, 'getstatus' : True, 'ata': True} )
#         return render( request, 'studenthome/index.html', context.flatten() )

# view to look or modify student data
def status(request, rollno):
    return HttpResponse("Status is disabled for now!" + time)
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

