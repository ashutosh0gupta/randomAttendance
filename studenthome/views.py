from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.
from django.template import loader, RequestContext
from django.http import HttpResponse
from .models import StudentInfo,Call,Question,StudentAnswers,SystemState,BioBreak,ExamRoom,Exam,ExamMark,SwitchSeat
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import PermissionRequiredMixin, AccessMixin,UserPassesTestMixin
from django.views.generic.edit import CreateView, DeleteView, UpdateView,FormView
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Q

import logging

import string
import csv
import os
import shutil
import datetime
import random
from collections import defaultdict
from io import StringIO
import pandas as pd
import hmac
import hashlib
import base64
# import pylatexenc
# from pylatexenc.latex2text import LatexNodes2Text

logq = logging.getLogger('quiz')

#----------------------------------------------------------------------------
# utils


#----------------------------------------------------------------------------

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
    return random.choice( student_list )

def clean_latex( s ):
    return s
    # return LatexNodes2Text().latex_to_text( s )

def log_and_message( request, s ):
    messages.success( request, s)
    logq.info( s )

#----------------------------------------------------------------------------
# VIEWS

# def login(request):
#     return HttpResponse("Not implemented yet!!")

# def logout(request):
#     return redirect( reverse("login") )

def get_user_rollno( u ):
    try:
        if( u.ldap_user ):
            rollno = u.ldap_user.attrs['employeeNumber']
            assert( len(rollno) > 0 )
            return rollno[0].upper()
        else:
            # test situation or local user 
            # where we do not care of ldap authenticaiton
            return u.username
    except AttributeError:
        return str(u.username)

def who_auth(request):
    u = request.user
    if u.is_anonymous:
        if settings.DEBUG:
            #------------------------
            # For testing
            #------------------------
            return '25B1818'
            # return "prof"
        return None
    #-----------------------------
    # Profs and the Head TAs
    #-----------------------------    
    if u.username in ["akg", "firuza", "ivarnam"]:
        return "prof"
    #-----------------------------
    # Other TAs
    #-----------------------------    
    if u.username in []:
        return "ta"    
    # -----------------------------------
    # if studentinfo is not found, the student is not
    # registered in the course OR logging in first time
    # -----------------------------------
    s = get_or_none( StudentInfo, username = u.username )
    if s == None:
        # -------------------------------------
        # Get user roll number via ldap records
        #  todo: throws an error if ldap
        #        is mis-configured
        # -------------------------------------
        rollno = get_user_rollno( u )
        # print('I am here:' + rollno)
        s = get_or_none( StudentInfo, pk = rollno )
        if s == None:
            # Student is not registered for the course
            return None
        else:
            s.username = u.username
            s.save()
            return s.rollno
    else:
        if s.isEnabled:
            return s.rollno
        else:
            return None

def get_q_op( q, idx ):
    op = q._meta.get_field("op"+str(idx))
    op_str = op.value_from_object( q )
    if op_str :
        return clean_latex( op_str ) # LatexNodes2Text().latex_to_text( op_str )
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

def is_ith_option_correct( sa, idx, q):
    op = sa._meta.get_field("op"+str(idx))
    op_num = op.value_from_object( sa )
    correct_ans = get_q_ans(q,op_num)
    ans = sa._meta.get_field("ans"+str(idx))
    student_ans = ans.value_from_object( sa )
    if correct_ans == student_ans :
        return (True,op_num)
    else:
        return (False,op_num)

# def is_answer_correct( sa ):
#     q = get_or_none( Question, pk=sa.q )
#     result = True
#     for idx in range(1,5):
#         is_correct, _ =  is_ith_option_correct( sa, idx, q)
#         if not is_correct:
#             result = False
#             break
#     return result

# to be removed and replaced by the above function
def is_answer_correct( sa ):
    q = get_or_none( Question, pk=sa.q )
    s = get_or_none( StudentInfo, pk=sa.rollno )
    result = True
    correct_count = 0
    for idx in range(1,5):
        op = sa._meta.get_field("op"+str(idx))
        op_num = op.value_from_object( sa )
        correct_ans = get_q_ans(q,op_num)
        ans = sa._meta.get_field("ans"+str(idx))
        student_ans = ans.value_from_object( sa )
        if correct_ans == student_ans :
            correct_count = correct_count + 1
            # result = False
            # break
    if correct_count == 4:
        return True,4
    else:
        return False,correct_count

def get_answer_status( sa ):
    if sa.answer_time == None:
        return 'ABSENT'
    elif sa.is_correct:
        return 'CORRECT'
    elif sa.correct_count == 3:
        return 'PART_CORRECT'
    else:
        return 'WRONG'
    
def find_first_active_question():
    for i in range(1,5):
        qid = get_active_q(i)
        if qid > 0:
            return qid
    return 0

#-------------------------------------------------------
# MAIN ENTRY POINT

def index(request):
    p = who_auth(request)
    if p == None:
        return redirect( reverse("logout") )
    context = RequestContext(request)
    s = get_sys_state()
    context["sys"] = s
    context[ "is_prof" ] = (p == "prof")
    if p == "prof":
        if s.mode == "QUIZ":
            logq.info( 'prof Quiz status request' )
            q = get_or_none( Question, pk=find_first_active_question() )
            # question on the screen
            if( q != None ):
                context["q"] = clean_latex( q.q) # LatexNodes2Text().latex_to_text( q.q )
                context["q_code"] = q.code
            else:
                context["q"] = ""
            context[ "students" ] = StudentInfo.objects.all()
            response = render( request, 'studenthome/quiz.html', context.flatten() )
            logq.info( 'prof Quiz status rendered' )
            return response # render( request, 'studenthome/quiz.html', context.flatten() )
        else:
            context[ "dayhash" ] = settings.DAYHASH
            return render( request, 'studenthome/dashboard.html', context.flatten() )
    # student is logged in
    if s.mode == "QUIZ":
        # q = get_or_none( Question, pk=s.activeq )
        sa = None
        for i in range(1,5):
            qid = get_active_q(i)
            local_sa = get_or_none( StudentAnswers, rollno=p, q=qid )
            if local_sa != None:
                sa = local_sa
                if sa.answer_time == None:
                    break
        if sa == None:
            return HttpResponse( "Something is wrong!!" )
        if sa.answer_time != None and (timezone.now()-sa.answer_time).total_seconds() < 30:
            url = reverse('index')
            return HttpResponse( f'<h3>Submitted.</h3><a href="{url}">Wait for 30 seconds to  see the results!</a>' )
        return redirect( reverse('answer', kwargs={'ansid':sa.pk}) )
    else:
        student = get_or_none( StudentInfo, rollno=p )
        context[ "student" ] = student

        scores = {}
        for c in student.course.split(':'):
            exams = Exam.objects.filter( Q(course = c) )
            escores = {}
            if exams:
                for exam in exams:
                    marks = ExamMark.objects.filter( Q(rollno = p)&Q(exam_id = exam.id) )
                    escores[exam] = marks
            scores[c] = escores
        context["scores"] = scores
        
        if s.next_exam >= datetime.date.today():
            context[ "next_exam" ] = s.next_exam
        else:
            context[ "next_exam" ] = None            
        return render( request, 'studenthome/dashboard.html', context.flatten() )
    

#---------------------------------------------------------
# view for loading student list from ASC website

def db_import(request):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )

    imported=''
    csv_file = os.path.expanduser('/tmp/output.csv')
    current_rolls = []
    os.makedirs('studenthome/images/', exist_ok=True)
    course = "***"
    try:
        with open(csv_file) as f:
            reader = csv.reader(f)
            num_created = 1
            for row in reader:
                student, created = StudentInfo.objects.get_or_create(
                    rollno=row[1]
                )
                current_rolls.append( row[1] )
                course = row[4]
                if created:
                    #--------------------------------------------
                    # for security, random prefix is added to the file paths
                    #--------------------------------------------
                    salt = ''.join(random.choices(string.ascii_lowercase, k=10))
                    #----------------------------------
                    # Update student records
                    #----------------------------------
                    student.name = row[2]
                    student.imagePath = salt+row[3]
                    student.isPwd = (row[5] == 'Yes')
                    student.calls = None
                    student.save()
                    #--------------------------------
                    # Copy photo to web reachable place
                    #--------------------------------
                    shutil.copy('/tmp/'+row[3],'studenthome/images/'+salt+row[3])
                    #------------------------------------
                    # Colleact info for imported students
                    #------------------------------------                
                    imported += row[1]+"," + row[2]+","+salt+row[3]+","+row[4]+"<br>"
                    num_created += 1
                #---------------------------------------------
                # Add course in the course list of the student
                #---------------------------------------------
                if not(row[4] in student.course):
                    if student.course == '---':
                        student.course = row[4]
                    else:
                        student.course = student.course+':'+row[4]
                    student.save()
                print( "processed: " + row[1] )
                if num_created > 100:
                    impported += "---- There may be more students; Run again ---- <br>"
                    break
    except IOError as e:
        return HttpResponse( "Failed to open file "+csv_file + ".<br> Look into README for importing students!")
    deleted  = "The following students are not in the rolls.<br>"
    # deleted += "to be deleted students:<br>"
    # deleted += "(To avoid accedental deletion, user needs to do it manually."
    # deleted += "goto to the student page)<br>"
    student_list = StudentInfo.objects.order_by('rollno')
    any_deleted = False
    for student in student_list:
        if (student.rollno not in current_rolls) and (course in student.course):
            deleted += "<a href=\"/" + student.rollno + "\">" + student.rollno + "</a><br>"
            any_deleted = True
    if not any_deleted:
        deleted = ''
    logq.info( 'Import ran!' )
    return HttpResponse(imported+deleted)

def create_local_users(request):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )

    sas = []
    m = {}
    created = ''
    num_created = 1
    for s in StudentInfo.objects.all():
        u = get_or_none( User, username=s.rollno )
        if u == None: 
            passwd = get_random_string(8)
            sas.append( User(
                username=s.rollno,
                email=s.rollno+'@iitb.ac.in',
                password=make_password(passwd),
                is_active=True,
            ) )
            # sas.append( User( username=s.rollno,  password= passwd) )
            print( s.rollno + "," + passwd )
            created += s.rollno + "," + passwd+"<br>"
            num_created += 1
            if num_created > 100:
                created += "---- More students to be processed; RUN AGAIN --<br>"
                break
    User.objects.bulk_create( sas )
    if created == '':
        created = 'No users were created! All already exist!'
    created += 'Save this passwords, you will not be able to see them again!'
    logq.info( 'create local user ran!' )
    return HttpResponse(created)

class EditStudentInfo(UpdateView):
    model = StudentInfo
    fields = ['course','absent','isPwd','isEnabled']
    template_name = 'studenthome/studentinfoedit.html'
    pk_url_kwarg = 'sid'
    
    def get_context_data( self, **kwargs ):
        context = super(EditStudentInfo,self).get_context_data(**kwargs)
        s = self.object
        context[ "is_auth" ] = (who_auth( self.request ) == 'prof')
        context[ "student" ] = s
        return context

    def form_valid(self,form):
        try:
            u = who_auth( self.request )
            if  u != "prof": raise Exception( f'[Attack] non prof  {u} is modifying student' )
            return super().form_valid(form)
        except Exception as e:
            logq.error( '{}!'.format(e) )
            form.add_error( None, '{}!'.format(e) )
            return redirect( reverse( 'index' ) )

    def get_success_url(self):
        s = self.object
        log_and_message( self.request, f'Student {s.rollno} edited!' )
        return reverse( "all" )

# def question(request):
#     if is_student(request):
#         return student_attempt(attempt)
#     if is_prof(request):
#         return show_question(attempt)
#     return HttpResponse( 'No login or unregistered user!' )        

#--------------------------------------------------------------------
# question creation and management
#--------------------------------------------------------------------

q_fields = ['q','code','course']
op_fields = []
ans_fields = []
for i in range(1,21):
    q_fields.append('op'+str(i))
    q_fields.append('ans'+str(i))
    op_fields.append('op'+str(i))
    ans_fields.append('ans'+str(i))

def clean_ops( ss ):
    ls = ss.split('\n')
    ls = [ s.strip() for s in ls]
    return list(filter( None, ls ))
        
class CreateQuestion(SuccessMessageMixin,CreateView):
    model = Question
    fields= ['q','code','course','trues','falses'] #q_fields
    # fields= ['q','trues','falses','fillCode','checkCode']
    template_name = 'q/create.html'

    def get_context_data( self, **kwargs ):
        context = super(CreateQuestion,self).get_context_data(**kwargs)
        context[ "is_auth" ] = (who_auth( self.request ) == "prof")
        context[ "qs" ] = Question.objects.all().order_by("-id")
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
            
            response = super().form_valid(form)
            d = self.object

            t_ops = clean_ops(d.trues)
            f_ops = clean_ops(d.falses)
            total_op_nums =len(t_ops)+len(f_ops)
            if total_op_nums > 20 or total_op_nums < 4:
                raise Exception( "Out of range number of options :" + str(total_op_nums) )

            # save options on the object
            idx = 1
            for t_op in t_ops:
                setattr(d, f'op{idx}', t_op)
                setattr(d, f'ans{idx}', True)
                idx = idx+1
            for f_op in f_ops:
                setattr(d, f'op{idx}', f_op)
                setattr(d, f'ans{idx}', False)
                idx = idx+1

            # Normalize course names
            d.course = d.course.replace(" ", "").upper() 
            d.save()

            # view options on the command line
            for op_name in op_fields:
                op = d._meta.get_field(op_name)
                op_str = op.value_from_object(d)
                if op_str :
                    uni_op = clean_latex( op_str ) #LatexNodes2Text().latex_to_text(op_str)
                    print(uni_op)
            messages.success(self.request,'Created question '+str(d.id)+'!')

            # ---------------------------------
            # bulk create for student resonses
            # --------------------------------
            #
            # ops = get_active_options( d )
            # sas = []
            # for s in StudentInfo.objects.all():
            #     op = random.sample( ops, 4 )
            #     sas.append( StudentAnswers(rollno=s.rollno, q=d.pk,
            #                                op1 = op[0], op2 = op[1],
            #                                op3 = op[2],op4 = op[3] ) )
            # StudentAnswers.objects.bulk_create( sas )
            #

            logq.info( 'Question ' + str(d.pk) + ' created.' )

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
    template_name = 'q/edit.html'
    pk_url_kwarg = 'qid'
    
    def get_context_data( self, **kwargs ):
        context = super(EditQuestion,self).get_context_data(**kwargs)
        context[ "is_auth" ] = (who_auth( self.request ) == "prof")
        return context

    def form_valid(self,form):
        try:
            u = who_auth( self.request )
            if  u != "prof": raise Exception( f'[Attack] non prof  {u} is modifying a question' )
            return super().form_valid(form)
        except Exception as e:
            logq.error( '{}!'.format(e) )
            form.add_error( None, '{}!'.format(e) )
            return redirect( reverse( 'index' ) )

    def get_success_url(self):
        q = self.object
        logq.info( 'Question ' + str(q.id) + ' edited.' )
        return reverse( "createq" )

def deleteq(request, qid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    q = get_or_none( Question, pk = int(qid) )
    # -------------------------------------------
    # Clear student submissions
    # -------------------------------------------
    StudentAnswers.objects.filter(q=qid).delete()
    
    if q:
        # -------------------------------------------
        # Update attendance count!
        # -------------------------------------------
        if q.first_activation_time != None:
            # if quiz has been attempted
            sys = get_sys_state()
            sys.num_attendance = sys.num_attendance - 1
            sys.save()
        # -------------------------------------------
        # Delete the question
        # -------------------------------------------
        q.delete()
        # -------------------------------------------
        # Report the deletion
        # -------------------------------------------
        log_and_message( request, 'Question ' + str(qid) + ' deleted.' )
        # messages.success(request,'Question '+str(q.id)+' deleted!')
        # logq.info( 'Question ' + str(qid) + ' deleted.' )
 
    # -------------------------------------------
    # Redirect to create quetion page!
    # -------------------------------------------
    return redirect( reverse( 'createq' ) )


def swapq(request, qid1, qid2 ):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )

    # -------------------------------------------
    # Find the questions
    # -------------------------------------------    
    q1 = get_or_none( Question, pk = int(qid1) )
    q2 = get_or_none( Question, pk = int(qid2) )

    # -------------------------------------------
    # Clear student submissions
    # -------------------------------------------
    # StudentAnswers.objects.filter(q=qid1).delete()
    # StudentAnswers.objects.filter(q=qid2).delete()
    
    if q1 and q2:
        messages.success(request,f'Questions {q1.id} and {q2.id} swapped!')
        q1.id = qid2
        q2.id = qid1
        q1.save()
        q2.save()
        logq.info( f'Questions {q1.id} and {q2.id} swapped!' )
 
    # -------------------------------------------
    # Redirect to create quetion page!
    # -------------------------------------------
    return redirect( reverse( 'createq' ) )

def shiftq(request, qid1, qid2 ):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    qid1= int(qid1)
    qid2= int(qid2)
    if qid1 >= qid2:
        return HttpResponse( 'Incorrect shift parameters!' )
        

    # -----
    # The following code is incorrect needs fixing
    #-----
    assert(False)
    for q in range(qid2,qid1,-1):
        q1 = get_or_none( Question, pk = q )
        q2 = get_or_none( Question, pk = q-1 )
        if q1 and q2:
            messages.success(request,f'Questions {q1.id} and {q2.id} swapped!')
            q1.id = q-1
            q2.id = q
            q1.save()
            q2.save()
            logq.info( f'Questions {q1.id} and {q2.id} swapped!' )
            
    
    # -------------------------------------------
    # Redirect to create quetion page!
    # -------------------------------------------
    return redirect( reverse( 'createq' ) )


def viewq(request, qid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    q = get_or_none( Question, pk = int(qid) )
    ops = dict()
    corrects = dict()
    wrongs = dict()
    for i in range(1,21):
        ops['op'+str(i)] = get_q_op( q, i )
        corrects['c_num_'+str(i)] = 0
        wrongs['w_num_'+str(i)] = 0        
    sas = StudentAnswers.objects.filter( q = q.pk ).exclude(answer_time = None ).all()
    for sa in sas:
        for idx in range(1,5):
            is_correct, op_num =  is_ith_option_correct( sa, idx, q)
            if is_correct:
                corrects['c_num_'+str(op_num)] += 1
            else:
                wrongs['w_num_'+str(op_num)] += 1                
    context = RequestContext(request)
    context.push( {'q': q } )
    context.push( ops )
    context.push( corrects )
    context.push( wrongs )
    return render( request, 'q/view.html', context.flatten() )

#------------------------------------
# System state
#------------------------------------

def get_sys_state():
    s, created = SystemState.objects.get_or_create(pk = 1)
    return s

def get_active_q( i, sys = None ):
    if sys == None: sys = get_sys_state()
    op = sys._meta.get_field("activeq"+str(i))
    return op.value_from_object( sys )

def put_active_q( i, qid ):
    sys = get_sys_state()
    if i == 1:
        sys.activeq1 = qid
    elif i == 2:
        sys.activeq2 = qid
    elif i == 3:
        sys.activeq3 = qid
    elif i == 4:
        sys.activeq4 = qid        
    sys.save()
        
def activateq(request, iid, qid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )

    iid=int(iid)
    qid = int(qid)
    for i in range(1,5):
        # print(iid)
        # print(i)
        if iid == i:
            # update qid
            put_active_q( iid, qid )
        else:
            # qid is not repeated
            if get_active_q(i) == qid:
                put_active_q(i,0)

    #update system state
    # sys = get_sys_state()
    # sys.activeq = qid
    # sys.save()
    
    logq.info( 'Question ' + str(qid) + ' at ' + str(iid) +' activated.' )

    return redirect( reverse( 'createq' ) )

def deactivateq(request, iid):
    if who_auth(request) != 'prof':
        return HttpResponse( 'Incorrect login!' )

    put_active_q( int(iid), 0 )
    logq.info( 'Idx ' + iid +' deactivated.' )
    return redirect( reverse( 'createq' ) )

def update_nextexamdate(request, date):
    if who_auth(request) != 'prof':
        return HttpResponse( 'Incorrect login!' )
    sys = get_sys_state()
    

class EditNextExamDate(UpdateView):
    model = SystemState
    fields = ['next_exam']
    template_name = 'exam/examdate.html'
    pk_url_kwarg = 'rid'
    
    def get_context_data( self, **kwargs ):
        context = super(EditNextExamDate,self).get_context_data(**kwargs)
        context[ "is_auth" ] = (who_auth( self.request ) == "prof")
        return context

    def form_valid(self,form):
        try:
            u = who_auth( self.request )
            if  u != "prof": raise Exception( f'[Attack] non prof  {u} is modifying exam date' )
            return super().form_valid(form)
        except Exception as e:
            logq.error( '{}!'.format(e) )
            form.add_error( None, '{}!'.format(e) )
            return redirect( reverse( 'index' ) )

    def get_success_url(self):
        sys = self.object
        logq.info( 'Next Exam date updated ' + str(sys.next_exam) + ' edited.' )
        return reverse( "createexam" )

#-----------------------------------------------------------------------------
# Running quiz
#-----------------------------------------------------------------------------

def quiz_status( q_statuses ):
    any_part    = 'PART_CORRECT' in q_statuses
    any_wrong   = 'WRONG' in q_statuses
    any_correct = 'CORRECT' in q_statuses
    if 'ABSENT' in q_statuses:
        if any_wrong  or any_correct:
            return 'PART_FINISHED'
        else:
            return 'ABSENT'
    else:
        if any_wrong or any_part:
            if any_correct or any_part:
                return 'PART_CORRECT'
            else:
                return 'WRONG'
        else:
            return 'CORRECT'
        
@transaction.atomic
def bulk_update_student_status(qs):
    to_be_saved = []
    for s in StudentInfo.objects.all():
        statuses = []
        for q in qs:
            sa = get_or_none( StudentAnswers, rollno=s.rollno, q=q.pk )
            statuses.append( get_answer_status( sa ) )
        # only needs db change if multiple quizzes were executed
        status = quiz_status( statuses )
        if status != s.curr_status:
            s.curr_status = status
            s.save()

def startq(request):
    # check authentication
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )

    sys = get_sys_state()

    # check mode
    if sys.mode == 'QUIZ':
        return redirect( reverse( 'index' ) )


    # collect active active questions
    q1 = get_or_none( Question, pk=sys.activeq1 )
    q2 = get_or_none( Question, pk=sys.activeq2 )
    q3 = get_or_none( Question, pk=sys.activeq3 )
    q4 = get_or_none( Question, pk=sys.activeq4 )    
    qs = []
    reset_student_status = False
    for q in [q1,q2,q3,q4]:
        if q == None:
            continue
        qs.append(q)
        if q.first_activation_time == None:
            q.first_activation_time = timezone.now() #datetime.datetime.now()
            q.save()
            sys.num_attendance = sys.num_attendance + 1
            reset_student_status = False
    qs.reverse()           
    # reset students
    if reset_student_status:
        StudentInfo.objects.update( curr_status = 'ABSENT')
        
    
    ss = StudentInfo.objects.all()

    # ------------------------------------------------------------
    # If questions are old we need to bulk create the answer objects
    # ------------------------------------------------------------
    sas = []
    for s in StudentInfo.objects.all():
        for q in qs:
            sa = get_or_none( StudentAnswers, rollno=s.rollno, q=q.pk )
            if sa == None:
                ops = get_active_options( q )                
                op = random.sample( ops, 4 )
                sas.append( StudentAnswers(rollno=s.rollno, q=q.pk,
                                           op1 = op[0], op2 = op[1],
                                           op3 = op[2],op4 = op[3] ) )
    StudentAnswers.objects.bulk_create( sas )

    bulk_update_student_status(qs)
            
    sys.mode = 'QUIZ'
    sys.save()

    logq.info( 'Quiz for Question ' + str(sys.activeq1) + str(sys.activeq2) + str(sys.activeq3) +str(sys.activeq4) + ' is started.' )

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
    s4 = None
    s5 = None
    if len(student_list) > 5:
        #todo: remove this loop
        s_list = []
        for s in student_list:
            s_list.append(s)
        s1,s2,s3,s4,s5 = random.sample( s_list, 5 )
    else:
        if len(student_list) > 4: s5 = student_list[4]
        if len(student_list) > 3: s4 = student_list[3]
        if len(student_list) > 2: s3 = student_list[2]
        if len(student_list) > 1: s2 = student_list[1]            
        if len(student_list) > 0: s1 = student_list[0]
    context = RequestContext(request)
    context.push( {'s1': s1, 's2': s2, 's3': s3, 's4': s4, 's5': s5 } )
    logq.info( 'Quiz for Question ' + str(sys.activeq1) + str(sys.activeq2) + str(sys.activeq3) +str(sys.activeq4) + ' is stopped.' )

    return render( request, 'studenthome/results.html', context.flatten() )

#------------------------------------------------------------------------------
# Student answering quiz
#------------------------------------------------------------------------------

def calculate_student_status(s, known_sa = None, sys = None):
    statuses = []
    for i in range(1,5):
        qid = get_active_q( i, sys )
        if qid > 0:
            if known_sa.q == qid:
                sa = known_sa
            else:
                sa = get_or_none(StudentAnswers,rollno=s.rollno, q=qid)
            statuses.append( get_answer_status( sa ) )
    return quiz_status( statuses )

# @transaction.atomic
def update_student_status( rollno ):
    s = get_or_none(StudentInfo, pk=rollno)
    s.curr_status = calculate_student_status(s)
    s.save()

# @transaction.atomic
# def update_student_answer( sa ):
#     sa.answer_time = timezone.now() 
#     sa.is_correct,c_count = is_answer_correct( sa )
#     sa.correct_count = c_count
#     sa.save()
#     logq.info( str(sa.rollno) + ' answer-saved-'+str(c_count)+'.' )
            
#     # ----------------------------------------
#     # update student
#     # ----------------------------------------
#     update_student_status(sa.rollno)

class StudentResponse(UpdateView):
    model = StudentAnswers
    fields = ['ans1','ans2','ans3','ans4', 'user_agent']
    template_name = 'studenthome/answer.html'
    pk_url_kwarg = 'ansid'
    
    def get_context_data( self, **kwargs ):
        context = super(StudentResponse,self).get_context_data(**kwargs)
        sa = self.object
        q = get_or_none( Question, pk=sa.q )
        sys = get_sys_state()
        
        # identifiy the next and previous quiz id 
        idx = 0
        nxt = None
        prv = None
        q_num = 1
        is_old_quiz = True
        for i in range(1,5):
            qid = get_active_q( i )
            if idx > 0 and qid > 0:
                nxt = get_or_none(StudentAnswers,rollno=sa.rollno, q=qid)
                break
            if idx == 0 and qid > 0 and qid != sa.q:
                prv = get_or_none(StudentAnswers,rollno=sa.rollno, q=qid)
                q_num = q_num + 1
            if qid == sa.q:
                is_old_quiz = False
                idx = i
        if is_old_quiz:
            prv = None

        if (sys.mode != 'QUIZ'): is_old_quiz = True
            
        # get_sys_state()
        # populate context
        if sa.answer_time :
            context[ "yet_to_answer" ] = False
            context[ "q_ans1" ] = get_q_ans( q, sa.op1 )
            context[ "q_ans2" ] = get_q_ans( q, sa.op2 )
            context[ "q_ans3" ] = get_q_ans( q, sa.op3 )
            context[ "q_ans4" ] = get_q_ans( q, sa.op4 )
        else:
            context[ "yet_to_answer" ] = (sys.mode == 'QUIZ')

        context[ "is_auth" ] = ( who_auth( self.request ) == sa.rollno )
        context[ "sys" ] = sys
        # sa = get_or_none( StudentAnswers, ansid )
        # if sa == None:
        #     return HttpResponse( "Something is wrong!!" )
        context["q_name"] = clean_latex( q.q ) # LatexNodes2Text().latex_to_text( q.q )
        context["op1"] = get_q_op( q, sa.op1 )
        context["op2"] = get_q_op( q, sa.op2 )
        context["op3"] = get_q_op( q, sa.op3 )
        context["op4"] = get_q_op( q, sa.op4 )
        context["sa"] = sa
        context["q_course"] = q.course
        context["q_code"] = q.code
        context["q_num"] = q_num
        context["prev"] = prv # link to the previous question
        context["next"] = nxt # link to the next question
        context["is_old_quiz"] = is_old_quiz

        return context

    #@transaction.atomic
    def form_valid(self,form):
        try:
            sa = self.object

            # ----------------------------------------
            # Check if the answer is already submitted
            # ----------------------------------------
            if sa.answer_time :
                raise Exception( str(sa.rollno) + ' has already submitted!' )
            else:
                logq.info( str(sa.rollno) + ' submitting.' )
            
            # ----------------------------------------
            # Check user/system state is good!
            # ----------------------------------------
            if who_auth( self.request ) != sa.rollno:
                user_id = who_auth( self.request )
                raise Exception( '[Attack] wrong student is trying to submit '+ str(user_id) + '!=' + str(sa.rollno) )
            sys = get_sys_state()
            if sys.mode != 'QUIZ': 
                raise Exception( str(sa.rollno) + ' submitting question ' + str(sa.q) + ', while quiz is closed.' )
            if sys.activeq1 != sa.q and sys.activeq2 != sa.q and sys.activeq3 != sa.q and sys.activeq4 != sa.q:
                raise Exception( str(sa.rollno) + ' is answering wrong question.' )
            
            # ----------------------------------------
            # saving the details of answers
            # ----------------------------------------
            # update_student_answer( sa )
            # sa = self.object
            response = super().form_valid(form)
            
            sa = self.object
            sa.answer_time = timezone.now() 
            sa.is_correct,c_count = is_answer_correct( sa )
            sa.correct_count = c_count
            # logq.info( str(sa.rollno) + ' answer-saved-'+str(c_count)+'.' )
            
            # ----------------------------------------
            # update student
            # ----------------------------------------
            s = get_or_none(StudentInfo, pk=sa.rollno)
            s.curr_status = calculate_student_status(s, sa, sys)

            def f():
                sa.save()
                s.save()
                logq.info( str(sa.rollno) + ' answered-' + str(sa.q)+'-'+str(c_count) )
            for i in range(0,3):
                try:
                    with transaction.atomic():
                        transaction.on_commit(f)
                    break
                except Exception as e:
                    logq.error( f'{e} - Retry for {sa.rollno}!' )
                
            
            logq.info( str(sa.rollno) + ' responded ' )
            
            return response
        except Exception as e:
            # No timing is saved
            logq.error( '{}!'.format(e) )
            form.add_error( None, '{}!'.format(e) )
            return redirect( reverse( 'index' ) )

    def get_success_url(self):
        # return reverse('answer', kwargs={'ansid':self.object.id})
        return reverse( "index" )


#-------------------------------------------------------
# view for status for all the students

def all_status(request):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    student_list = StudentInfo.objects.order_by('rollno')
    sys = get_sys_state()
    num_attendance = sys.num_attendance
    absent_count = 0
    present_count = 0
    device_map = dict()
    print_calls = dict()
    corrects = dict()
    three_corrects = dict()
    wrongs = dict()    
    attend_count_map = dict()
    for student in student_list:
        attendances = StudentAnswers.objects.filter( rollno = student.rollno ).exclude(answer_time = None ).all()
        # code for backward compatibility
        devs = []
        corrects[student.rollno] = 0
        three_corrects[student.rollno] = 0
        wrongs[student.rollno] = 0
        for sa in attendances:
            b,corr_count = is_answer_correct( sa )
            # dt = sa.answer_time.strftime("%m-%d")
            dt = sa.q
            devs.append( (sa.q, sa.user_agent) )
            if dt in attend_count_map:
                attend_count_map[dt] = attend_count_map[dt] + 1
            else:
                attend_count_map[dt] = 1
            if b != sa.is_correct or corr_count != sa.correct_count:
                sa.is_correct = b
                sa.correct_count = corr_count
                sa.save()
            if b:
                corrects[student.rollno] = corrects[student.rollno] + 1
            elif corr_count == 3:
                three_corrects[student.rollno] = three_corrects[student.rollno] + 1
            else:
                wrongs[student.rollno] = wrongs[student.rollno] + 1
        present_count = present_count +  len(attendances)
        print_calls[student.rollno] = attendances
        device_map[student.rollno] = devs
    #----------------------------
    # Analyzing device map
    #----------------------------
    reverse_dev_map = dict()
    dev_map_set = dict()
    for rollno,devs in device_map.items():
        for (q,dev) in devs:
            if dev in reverse_dev_map:
                reverse_dev_map[dev].append((q,rollno))
            else:
                reverse_dev_map[dev] = [(q,rollno)]
        dev_map_set[rollno] = set([ dev for _,dev in devs ])
        
    problematic_match = []
    for rollno1,devs1 in dev_map_set.items():
        for rollno2,devs2 in dev_map_set.items():
            if rollno1 >= rollno2: continue
            if len(set.intersection(devs1,devs2)) > 1:
                problematic_match.append( (rollno1, rollno2) )
                
                
    presence_rate = 0
    total_calls = num_attendance*len(student_list)
    if total_calls > 0:
        presence_rate = (100*present_count)/total_calls
    context = RequestContext(request)
    context.push( {'student_list': student_list,
                   'presence_rate': presence_rate,
                   'attend_count_map': attend_count_map,
                   'num_attendance': num_attendance,
                   'device_map'  : reverse_dev_map,
                   'problematic_fingerprint_match'  : problematic_match,
                   'print_calls' : print_calls,
                   'corrects' : corrects,
                   'wrongs' : wrongs,
                   'three_corrects' : three_corrects,                   
                    'show_photo' : True, } )
    return render( request, 'studenthome/all.html', context.flatten() )

    

#======================================================
# Old random views

# view to see a random student
def call(request):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )    
    student_list = StudentInfo.objects.exclude( curr_status = 'ABSENT' ).all()
    
    if len(student_list) == 0:
        return HttpResponse("No students in the class!!")
    else:
        student = pick_a_student( student_list )
        context = RequestContext(request)
        context.push( {'student': student, 'getstatus' : True, } )
        return render( request, 'studenthome/index.html', context.flatten() )


# view to look or modify student data
def status(request, rollno):
    return HttpResponse("Status is disabled for now!")
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
            # student_calls = get_call_list( student )
            # for c in reversed(student_calls):
            #     c.delete()
            # student.calls = None
            # student.save()
            student.delete()
            return HttpResponse( "Student for roll number " + str(rollno) + " has been removed." )
        return redirect( "/"+str(student.rollno)+"/" )
    else:
        # call_list = get_call_list( student )
        context = RequestContext(request)
        context.push( {'student': student, 'getstatus' : False } )
        return render( request, 'studenthome/index.html', context.flatten() )

#-----------------------------------------
# Biobreak
#-----------------------------------------

def biobreak_actives():
    acts = BioBreak.objects.filter( Q(returned_time=None) & ~Q(activate_time=None)).all().order_by('activate_time')
    return acts

def biobreak_queue():
    bbs = BioBreak.objects.filter( Q(returned_time=None) & Q(activate_time=None)).all().order_by('request_time')
    return bbs

def biobreak_returned():
    bbs = BioBreak.objects.filter( ~Q(returned_time=None) ).all().order_by('request_time')
    return bbs

def biobreak_active_by_area():
    acts = biobreak_actives()
    acts_dict = defaultdict(list)
    for act in acts: acts_dict[act.area].append(act)
    return acts_dict

def biobreak_queue_by_area():
    bbs = biobreak_queue()
    bbs_dict = defaultdict(list)
    for act in bbs: bbs_dict[act.area].append(act)
    return bbs_dict

def biobreak_next_access():
    actives_area = biobreak_active_by_area()
    queue_area  = biobreak_queue_by_area()
    #-------------------------------------------
    # Biobreak queue is divided by the area
    #--------------------------------------------
    for area in queue_area:
        queue = queue_area[area]
        #-------------------------------------------
        # Check if queue is not empty in the area
        #--------------------------------------------
        if len(queue) > 0:
            #-------------------------------------------
            # Check how many are active in the area
            #--------------------------------------------
            if area in actives_area:
                active = len(actives_area[area])
            else:
                active = 0
            #-------------------------------------------
            # Adaptive control: if wait time > 10x minute,
            # x+1 people can go for biobreak simultaneously
            #-------------------------------------------
            wait = 1+int((timezone.now()-queue[0].request_time).seconds/600)
            send_next = max( 1 - active, wait - active, 0 )
            send_next = min(send_next, len(queue))
            #-------------------------------------------
            # Send them for biobreak
            #-------------------------------------------
            for i in range(0,send_next):
                nbb = queue[i]
                nbb.activate_time = timezone.now()
                nbb.save()
        

class AddBioBreak(SuccessMessageMixin,CreateView):
    model = BioBreak
    fields= ['rollno']
    template_name = 'studenthome/biobreak.html'
    dayhash = settings.DAYHASH

    def get_context_data( self, **kwargs ):
        context = super(AddBioBreak,self).get_context_data(**kwargs)
        context[ "is_auth" ] = (self.kwargs.get('dayhash') == self.dayhash)
        biobreak_next_access()
        bbs  = biobreak_queue()
        # bbs = biobreak_returned()
        acts = biobreak_actives()
        remain_time = {}
        for act in acts:
            act.out_time = int((timezone.now()-act.activate_time).seconds/60)
        context[ "remain_time" ] = remain_time             
        context[ "acts" ] = acts             
        context[ "bbs" ] = bbs 
        context[ "sys" ] = get_sys_state()
        context[ "dayhash" ] = self.dayhash
        return context
    
    def get_success_url(self):
        return reverse( "biobreak", kwargs={'dayhash': self.kwargs.get('dayhash')} )

    def form_valid(self,form):
        try:
            d = None

            dayhash = self.kwargs.get('dayhash')
            if dayhash != self.dayhash:
                return HttpResponse( 'Incorrect access!' )
            
            response = super().form_valid(form)
            d = self.object
            d.rollno = d.rollno.upper()
            #----------------------------------------
            # Check if the student exists
            #----------------------------------------
            s = get_or_none( StudentInfo, pk = d.rollno )
            if s == None:
                raise Exception( "Student with rollno "+ d.rollno +" is not in the course!" )
            else:
                d.imagePath = s.imagePath
                d.area      = s.exam_area
                d.room      = s.exam_room
                d.seat      = s.exam_seat
            #----------------------------------------
            # Check if the student has alredy requested
            #----------------------------------------
            bbs = BioBreak.objects.filter(Q(returned_time=None) & Q(rollno=d.rollno)).all()
            if len(bbs) > 1:
                raise Exception( "Student with rollno "+ d.rollno +" is already on the queue!" )
            
            #----------------------------------------
            # Save the records of the request
            #----------------------------------------
            d.request_time = timezone.now() 
            d.save()

            #----------------------------------------
            # If Queue is empty new reuest gets to go
            #----------------------------------------
            biobreak_next_access()
            
            messages.success(self.request,'BioBreak Request Added '+str(d.id)+'!')

            logq.info( 'Biobreak request added ' + str(d.pk) + '.' )

            return response
        except Exception as e:
            # ---------------------------
            # Form validation failed, fill again
            # --------------------------
            form.add_error( None, '{}!'.format(e) )
            if d:
                d.delete()
            return super().form_invalid(form)

def biobreak_return(request,dayhash,rid):
    if dayhash != settings.DAYHASH:
        return HttpResponse( 'Incorrect access!' )
    bb = get_or_none( BioBreak, pk = rid )
    if bb:
        bb.returned_time = timezone.now()
        bb.save()
    biobreak_next_access()
    return redirect( reverse( 'biobreak', kwargs={'dayhash': dayhash}  ) )

def biobreak_urgent(request,dayhash,rid):
    if dayhash != settings.DAYHASH:
        return HttpResponse( 'Incorrect access!' )
    #----------------------------------------------------------------
    # Give urgent access
    #----------------------------------------------------------------
    bb = get_or_none( BioBreak, pk = rid )
    if bb:
        bb.activate_time = timezone.now()
        bb.save()
    return redirect( reverse( 'biobreak', kwargs={'dayhash': dayhash}  ) )

def biobreak_withdraw(request,dayhash,rid):
    if dayhash != settings.DAYHASH:
        return HttpResponse( 'Incorrect access!' )
    #-----------------------------------------------------------------
    # Withdraw request by setting both returned_time and activate_time
    #-----------------------------------------------------------------
    bb = get_or_none( BioBreak, pk = rid )
    if bb:
        time = timezone.now()
        bb.activate_time = time
        bb.returned_time = time
        bb.save()
    return redirect( reverse( 'biobreak', kwargs={'dayhash': dayhash}  ) )

#-----------------------------------------
# ExamRooms
#-----------------------------------------

def clean_seats( ss ):
    ls = ss.split('\n')
    ls = [ s.strip() for s in ls if s[0] != "#"]
    return list(filter( None, ls ))

def disabled_seats( ss ):
    ls = ss.split('\n')
    ls = [ s.strip() for s in ls if s[0] == "#"]
    return list(filter( None, ls ))

def remaining_seats( ss, used):
    ls = ss.split('\n')
    disabled = []
    unused = []
    for s in ls:
        s = s.strip()
        if s[0] == "#":
            disabled.append(s)
        elif not s in used:
            unused.append(s)
    return disabled,unused

# def lhc_sort_seats( seats ):
#     splits = [(s[1:],s[0]) for s in seats]
#     splits.sort()
#     return [ column+row for (row,column) in splits]

class CreateExamRoom(SuccessMessageMixin,CreateView):
    model = ExamRoom
    fields= ['name','area','seats'] #q_fields
    template_name = 'studenthome/examroomcreate.html'

    def get_context_data( self, **kwargs ):
        context = super(CreateExamRoom,self).get_context_data(**kwargs)
        context[ "is_auth" ] = (who_auth( self.request ) == "prof")
        for room in ExamRoom.objects.all():
            room.capacity = len(clean_seats(room.seats))
            room.disabled = len(disabled_seats(room.seats))
            room.save()
        context[ "examrooms" ] = ExamRoom.objects.all().order_by("name")
        return context
    
    def get_success_url(self):
        return reverse( "createexamroom" )

    def form_valid(self,form):
        try:
            d = None
            u = who_auth(self.request)
            if u == None:
                return redirect( reverse("logout") )
            if u != 'prof':
                raise Exception( "Wrong kind of login!" )
            
            response = super().form_valid(form)
            d = self.object
            d.name = d.name.upper() 
            d.area = d.area.upper()
            
            #----------------------------------------
            # Check if the student has alredy requested
            #----------------------------------------
            rooms = ExamRoom.objects.filter( name=d.name ).all()
            if len(rooms) > 1:
                raise Exception( "Room "+ d.name +" already exists!" )
            

            # Normalize course names
            d.save()

            messages.success(self.request,'Created room '+str(d.name)+'!')
            logq.info( 'Room ' + str(d.pk) + ' created.' )

            return response
        except Exception as e:
            # Form has failed fill gain
            form.add_error( None, '{}!'.format(e) )
            if d:
                d.delete()
            return super().form_invalid(form)


class EditExamRoom(UpdateView):
    model = ExamRoom
    fields = ['name','area','available','seats']
    template_name = 'studenthome/examroomedit.html'
    pk_url_kwarg = 'rid'
    
    def get_context_data( self, **kwargs ):
        context = super(EditExamRoom,self).get_context_data(**kwargs)
        context[ "is_auth" ] = (who_auth( self.request ) == "prof")
        return context

    def form_valid(self,form):
        try:
            u = who_auth( self.request )
            if  u != "prof": raise Exception( f'[Attack] non prof  {u} is modifying a question' )
            return super().form_valid(form)            
        except Exception as e:
            logq.error( '{}!'.format(e) )
            form.add_error( None, '{}!'.format(e) )
            return redirect( reverse( 'index' ) )
        
    def get_success_url(self):
        q = self.object
        logq.info( 'Question ' + str(q.id) + ' edited.' )
        return reverse( "createexamroom" )

def delete_exam_room(request, rid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    r = get_or_none( ExamRoom, pk = int(rid) )
    
    if r:
        # -------------------------------------------
        # Delete the room
        # -------------------------------------------
        r.delete()
        # -------------------------------------------
        # Report the deletion
        # -------------------------------------------
        messages.success(request,'Room '+str(r.id)+' deleted!')
        logq.info( 'Room ' + str(r.id) + ' deleted.' )
 
    # -------------------------------------------
    # Redirect to create quetion page!
    # -------------------------------------------
    return redirect( reverse( 'createexamroom' ) )

def enable_examroom(request, rid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    r = get_or_none( ExamRoom, pk = rid )
    if r:
        r.available = True
        r.save()
        messages.success(request,'Romm '+rid+' is available!')
        logq.info( 'Room ' + rid + ' is available!' )
    return redirect( reverse( 'createexamroom' ) )

def disable_examroom(request, rid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    r = get_or_none( ExamRoom, pk = rid )
    if r:
        r.available = False
        r.save()
        messages.success(request,'Romm '+rid+' is unavailable!')
        logq.info( 'Room ' + rid + ' is unavailable!' )
    return redirect( reverse( 'createexamroom' ) )

@transaction.atomic
def seating(request,cid, isRefresh):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )

    if isRefresh == 'refresh':
        # -------------------------------------------
        # Filter students by the course
        # -------------------------------------------    
        students = StudentInfo.objects.filter( Q(course__contains = cid) & Q(isPwd = False) ).order_by('?')
        pwds = StudentInfo.objects.filter( Q(course__contains = cid) & Q(isPwd = True) ).order_by('rollno')
        total = len(students) + len(pwds)

        available = []
        # -------------------------------------------
        # Collect seats
        # -------------------------------------------    
        for r in ExamRoom.objects.order_by('-capacity'):
            if r.available:
                area = r.area
                name = r.name
                seats = clean_seats(r.seats)
                for s in seats:
                    available.append( (name, area, s) )
        if len(available) < total:
            messages.error( request, f'Not enough seats! students: {total} seats: {len(available)}' )
            return redirect( reverse( 'createexamroom' ) )
        # -------------------------------------------
        # Assign seats
        # -------------------------------------------
        i = 0
        def assign_seat(s,i):
            room,area,seat= available[i]
            s.exam_area = area
            s.exam_room = room
            s.exam_seat = seat
            s.save()
            return i + 1

        for s in students: i = assign_seat(s,i)

        #-------------------------------------------
        # All pwd candidate must be in the same room
        #-------------------------------------------
        room = available[i][0]
        for j in range(i,i+len(pwds)):
            if available[j][0] != room:
                i = j # shift seats
                break
        if len(pwds) > len(available) - i:
            messages.error( request, f'Not able seat pwd students! Add a room with at least {len(pwds)} seats.' )
            return redirect( reverse( 'createexamroom' ) )
            
        for s in pwds    : i = assign_seat(s,i)
        return redirect( reverse('allocateseats', kwargs={'cid':cid,'isRefresh':'view'}) )
        
    # -------------------------------------------
    # Disaply assigned seats
    # -------------------------------------------
    rooms = ExamRoom.objects.all()
    room_map = {}
    disabled_map = {}
    unused_map = {}
    for room in rooms:
        if room.available:
            students = StudentInfo.objects.filter( Q(exam_room = room.name)&Q(course__contains = cid) ).order_by('exam_seat')
            used_seats  = [student.exam_seat for student in students]
            disabled_seats,unused_seats = remaining_seats( room.seats, used_seats)
            room_map[room.name] = students
            disabled_map[room.name] = ",".join(disabled_seats)
            unused_map[room.name] = ",".join(unused_seats)
            
    # students_by_roll = StudentInfo.objects.filter( Q(course__contains = cid) ).order_by('rollno')
    context = RequestContext(request)
    context[ "room_map"     ] = room_map
    context[ "disabled_map" ] = disabled_map
    context[ "unused_map"   ] = unused_map
    # context["students_by_roll"] = students_by_roll
    context["cid"] = cid
    return render( request, 'studenthome/seating.html', context.flatten() )

class CreateSwitchSeat(SuccessMessageMixin,CreateView):
    model = SwitchSeat
    fields= ['rollno','room','seat','reason']
    template_name = 'rooms/switchseat.html'

    def get_context_data( self, **kwargs ):
        context = super(CreateSwitchSeat,self).get_context_data(**kwargs)
        context[ "is_auth" ] = (who_auth( self.request ) == "prof")
        start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timezone.timedelta(days=1)
        print(start,end)
        context[ "switches" ] = SwitchSeat.objects.filter(time__range=(start, end)).order_by("time")
        # context[ "switches" ] = SwitchSeat.objects.all().order_by("time")
        return context
    
    def get_success_url(self):
        return reverse( "createswitchseat" )

    def form_valid(self,form):
        try:
            d = None
            u = who_auth(self.request)
            if u == None:
                return redirect( reverse("logout") )
            if u != 'prof':
                raise Exception( "Wrong kind of login!" )
            
            response = super().form_valid(form)
            d = self.object
            d.rollno = d.rollno.upper() 
            
            s = get_or_none( StudentInfo, pk = d.rollno )
            if s == None:
                raise Exception( "Student with rollno "+ d.rollno +" is not in the course!" )
            else:
                s.exam_seat = s.exam_seat + '->' + d.room + '-'+ d.seat
                s.save()

            d.time = timezone.now() 
            d.save()

            messages.success(self.request,'Created seat switch '+str(d.rollno)+'!')
            logq.info( 'Created seat switch ' + str(d.pk) + ' created.' )

            return response
        except Exception as e:
            # Form has failed fill gain
            form.add_error( None, '{}!'.format(e) )
            if d:
                d.delete()
            return super().form_invalid(form)

#--------------------------------------------------------------------
# Exam creation and management (BIG TODO)
#--------------------------------------------------------------------

#----------------------------------------
# Process marks of the students
#----------------------------------------
@transaction.atomic
def process_marks(d):
    if d.marks:        
        # -------------------------------------------
        # Read CSV file
        # -------------------------------------------
        marks = pd.read_csv(StringIO(d.marks.upper()))
        
        # -------------------------------------------
        # Detect columns
        # -------------------------------------------
        qs = []
        for q in marks.columns:
            if q[0] == "Q":
                qid = int(q[1:])
                comment = None
                if f"COMMENT{qid}" in marks.columns: comment = f"COMMENT{qid}"
                qs.append( (q, int(q[1:]), comment ) )
               
        # qs = [ (q,int(q[1:]),None) for q in marks.columns[1:] if q[0] == "q" ]
        
        # -------------------------------------------
        # Process marks for each student
        # -------------------------------------------
        for index, row in marks.iterrows():
            r = row['ROLL NO']
            for r in r.split("-"): 
                for qname,qid,qcomment in qs:
                    em,created = ExamMark.objects.get_or_create( rollno=r, exam_id=d.id, q=qid )
                    if pd.isna(row[qname]):
                        em.marks = 0
                    else:
                        em.marks = row[qname]
                    if qcomment != None: em.comment = row[qcomment]
                    em.save()

@transaction.atomic
def regrade_marks(e):
    if e.regrade:        
        marks = pd.read_csv(StringIO(e.regrade.upper()))
        qs = [ (q,int(q[1:])) for q in marks.columns[1:] ]
        for index, row in marks.iterrows():
            r = row['ROLL NO']
            for qname,qid in qs:
                em = get_or_none( ExamMark, rollno=r, exam_id=e.id, q=qid )
                if em == None: continue
                update = False
                # -------------------------------------------------------------
                # Update only if uploaded marks are different from latest marks 
                # -------------------------------------------------------------
                if em.response_time2 and em.is_accepted2:
                    if em.crib_marks2 != row[qname]:
                        em.crib_marks2 = row[qname]
                        em.is_accepted2   = True
                        em.response_time2 = timezone.now()
                        em.response2 = e.regrade_reason
                        em.save()
                elif em.response_time and em.is_accepted:
                    if em.crib_marks != row[qname]:
                        em.crib_marks2 = row[qname]
                        em.is_accepted2   = True
                        em.raise_time2    = timezone.now()
                        em.response_time2 = timezone.now()
                        em.response2 = e.regrade_reason
                        em.save()
                else:
                    if em.marks != row[qname]:
                        em.crib_marks    = row[qname]
                        em.is_accepted   = True
                        em.raise_time     = timezone.now()
                        em.response_time = timezone.now()
                        em.response = e.regrade_reason
                        em.save()

def process_questions(d):
    num_q = 0
    total = 0
    none_found = False
    for i in range(1,11):
        num = getattr(d, f"mark{i}" )
        if num:
            num_q = i
            total = total + num
            if none_found:
                raise Exception( "Marks are not contiguous!" )
        else:
            none_found = True
    d.total = total
    d.num_q = num_q

class CreateExam(SuccessMessageMixin,CreateView):
    model = Exam
    fields= ['name','course','weight','mark1', 'mark2', 'mark3', 'mark4', 'mark5', 'mark6', 'mark7', 'mark8', 'mark9', 'mark10','marks'] #q_fields
    template_name = 'exam/create.html'

    def get_context_data( self, **kwargs ):
        context = super(CreateExam,self).get_context_data(**kwargs)
        context[ "is_auth" ] = (who_auth( self.request ) == "prof")
        context[ "exams" ] = Exam.objects.all().order_by("name")
        return context
    
    def get_success_url(self):
        return reverse( "createexam" )

    def form_valid(self,form):
        try:
            d = None
            u = who_auth(self.request)
            if u == None:
                return redirect( reverse("logout") )
            if u != 'prof':
                raise Exception( "Wrong kind of login!" )
            
            response = super().form_valid(form)
            d = self.object
            # d.name = d.name.upper() 
            
            #----------------------------------------
            # Check if the exam is already created
            #----------------------------------------
            exams = Exam.objects.filter( name=d.name ).all()
            if len(exams) > 1:
                raise Exception( "Exam "+ d.name +" already exists!" )

            #----------------------------------------
            # Process marks for the questions
            #----------------------------------------
            process_questions(d)

            
            #----------------------------------------
            # Create crib link
            #----------------------------------------
            salt = str(timezone.now())+str(d.id)
            dig = hmac.new(str.encode(settings.SECRET_KEY), msg=str.encode(salt), digestmod=hashlib.sha256).digest()
            dh = base64.b64encode(dig).decode()[:-1]
            d.link  = ''.join(e for e in dh if e.isalnum())
           
            #----------------------------------------
            # Process marks of the students
            #----------------------------------------
            process_marks(d)

            #----------------------------------------
            # Disable crib at the start
            #----------------------------------------
            d.is_cribs_active = False
            
            #----------------------------------------
            # Save the exam
            #----------------------------------------                    
            d.save()
            messages.success(self.request,'Created exam '+str(d.name)+'!')
            logq.info( 'Exam ' + str(d.name) + ' created.' )

            return response
        except Exception as e:
            # Form has failed fill gain
            form.add_error( None, '{}!'.format(e) )
            if d:
                d.delete()
            return super().form_invalid(form)

class EditExam(UpdateView):
    model = Exam
    fields = ['name','course','weight',
              'mark1', 'mark2', 'mark3', 'mark4', 'mark5',
              'mark6', 'mark7', 'mark8', 'mark9', 'mark10',
              'marks','is_cribs_active']
    template_name = 'exam/edit.html'
    pk_url_kwarg = 'rid'
    
    def get_context_data( self, **kwargs ):
        context = super(EditExam,self).get_context_data(**kwargs)
        context[ "is_auth" ] = (who_auth( self.request ) == "prof")
        return context

    def form_valid(self,form):
        try:
            u = who_auth( self.request )
            if  u != "prof": raise Exception( f'[Attack] non prof  {u} is modifying an exam' )
            return super().form_valid(form)
        except Exception as e:
            logq.error( '{}!'.format(e) )
            form.add_error( None, '{}!'.format(e) )
            return redirect( reverse( 'index' ) )

    def get_success_url(self):
        q = self.object
        #----------------------------------------
        # Process marks of the students
        #----------------------------------------
        process_marks(q)
        process_questions(q)
        q.save()
        logq.info( 'Question ' + str(q.name) + ' edited.' )
        return reverse( "createexam" )

class RegradeExam(UpdateView):
    model = Exam
    fields = ['regrade','regrade_reason']
    template_name = 'exam/regrade.html'
    pk_url_kwarg = 'rid'
    
    def get_context_data( self, **kwargs ):
        context = super(RegradeExam,self).get_context_data(**kwargs)
        context[ "is_auth" ] = (who_auth( self.request ) == "prof")
        context[ "e" ] = self.object
        return context

    def form_valid(self,form):
        try:
            u = who_auth( self.request )
            if  u != "prof": raise Exception( f'[Attack] non prof  {u} is regrading an exam!' )
            return super().form_valid(form)
        except Exception as e:
            logq.error( '{}!'.format(e) )
            form.add_error( None, '{}!'.format(e) )
            return redirect( reverse( 'index' ) )

    def get_success_url(self):
        e = self.object
        #----------------------------------------
        # Process marks of the students
        #----------------------------------------            
        regrade_marks(e)
        
        logq.info( 'Exame ' + str(e.name) + ' regraded!' )
        return reverse( "createexam" )


def delete_exam(request, rid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    r = get_or_none( Exam, pk = rid )
    
    if r:
        # -------------------------------------------
        # Delete the room
        # -------------------------------------------
        r.delete()
        # -------------------------------------------
        # Report the deletion
        # -------------------------------------------
        messages.success(request,'Exam '+rid+' deleted!')
        logq.info( 'Exam ' + rid + ' deleted.' )
 
    # -------------------------------------------
    # Redirect to create exam page!
    # -------------------------------------------
    return redirect( reverse( 'createexam' ) )

#--------------------------------------
# Returns scors,history
#--------------------------------------
def get_score( exammark ):
    if exammark:
        # ---------------------------
        # Instructor crib
        # ---------------------------
        if exammark.raise_time2 or exammark.is_accepted2:
            if exammark.is_accepted:
                crib_score = f"{exammark.marks}->{exammark.crib_marks}"
                past_score = exammark.crib_marks
            else:
                crib_score = f"{exammark.marks}->REJ"
                past_score = exammark.marks
            if exammark.is_accepted2:
                return exammark.crib_marks2,f"{crib_score}->{exammark.crib_marks2}"
            elif exammark.response_time2:
                return past_score,f"{crib_score}->REJ"
            else:
                return past_score,f"{crib_score}->RAISED"
                            

        # ---------------------------
        # TA cribs
        # ---------------------------
        if exammark.raise_time or exammark.is_accepted:
            if exammark.is_accepted:
                return exammark.crib_marks,f"{exammark.marks}->{exammark.crib_marks}"
            if exammark.response_time:
                return exammark.marks,f"{exammark.marks}->REJ"
            else:
                return exammark.marks,f"{exammark.marks}->Raised"                
        return exammark.marks,f"{exammark.marks}"
    else:
        # logq.info( 'Exammark is not found!' ) # cluttering the logs
        return 0,"0[Not uploaded]"

def view_exam(request, rid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )    
    context = RequestContext(request)
    
    exam = get_or_none( Exam, pk = rid )
    if exam:
        # ---------------------------------------------------------
        # Get students who are registered in the course of the exam
        # ---------------------------------------------------------
        students = StudentInfo.objects.filter( Q(course__contains = exam.course) ).order_by('rollno')
        scores= []
        for s in students:
            student_score  = [] 
            total = 0
            # ---------------------------------------------------------
            # Enumerate all questions of the exam
            # ---------------------------------------------------------
            for qid in range(1,exam.num_q+1):
                score = get_or_none( ExamMark, exam_id = exam.id, rollno=s.rollno, q=qid )
                # ----------------------------------------------
                # Returns latest score and the history of change
                #-----------------------------------------------
                marks,history = get_score(score)
                student_score.append( history )
                total += marks
            scores.append( [s.rollno,total]+student_score)
        # -------------------------------
        # Update context for the template
        # -------------------------------
        context["scores"] = scores
        context["exam"  ] = exam
        context["qs"    ] = [i for i in range(1,exam.num_q+1)]
        return render( request, 'exam/view.html', context.flatten() )
    else:
        return HttpResponse( 'Incorrect access!' )


def disable_crib(request, rid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    e = get_or_none( Exam, pk = rid )
    if e:
        e.is_cribs_active = False
        e.save()
        messages.success(request,'Cribs for exam '+rid+' deactivated!')
        logq.info( 'Cribs for exam ' + rid + ' deactivated!' )
    return redirect( reverse( 'createexam' ) )

def enable_crib(request, rid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    e = get_or_none( Exam, pk = rid )
    if e:
        e.is_cribs_active = True
        e.save()
        messages.success(request,'Cribs for exam '+rid+' activated!')
        logq.info( 'Cribs for exam ' + rid + ' activated!' )
    return redirect( reverse( 'createexam' ) )

def view_cribs(request, eid, qid, link):
    context = RequestContext(request)
    exam = get_or_none( Exam, pk = eid, link = link, is_cribs_active = True )
    if exam:
        cribs = ExamMark.objects.filter( Q(q = qid)&(~Q(raise_time = None))&Q(exam_id = exam.id)&Q(response_time = None) ).order_by('raise_time')
        dones = ExamMark.objects.filter( Q(q = qid)&(~Q(raise_time = None))&Q(exam_id = exam.id)&(~Q(response_time = None)) ).order_by('response_time')
        context["appeal"] = False
        context["cribs"] = cribs
        context["dones"] = dones
        context["qid"  ] = qid
        context["link" ] = link
        context["exam" ] = exam
        return render( request, 'exammark/cribs.html', context.flatten() )
    else:
        return HttpResponse( 'Crib session for this exam is disabled for now!' )

def exam_crib_links(request, eid, link):
    context = RequestContext(request)
    exam = get_or_none( Exam, pk = eid, link = link )
    if exam:
        context["exam"] = exam
        context["qs"] = [i for i in range(1,exam.num_q+1)]
        return render( request, 'exam/criblinks.html', context.flatten() )
    else:
        return HttpResponse( 'Incorrect access!' )

def view_cribs2(request, eid):
    if who_auth(request) != 'prof': return HttpResponse( 'Incorrect login!' )    
    context = RequestContext(request)
    exam = get_or_none( Exam, pk = eid )
    cribs = ExamMark.objects.filter( (~Q(raise_time2 = None))&Q(exam_id = exam.id)&Q(response_time2 = None) ).order_by('raise_time2')
    dones = ExamMark.objects.filter( (~Q(raise_time = None))&Q(exam_id = exam.id)&(~Q(response_time2 = None)) ).order_by('response_time2')
    context["appeal"] = True
    context["cribs"] = cribs
    context["dones"] = dones
    context["exam" ] = exam
    return render( request, 'exammark/cribs.html', context.flatten() )
    

#-------------------------------
# Crib management
#-------------------------------

class RaiseCrib(UpdateView):
    model = ExamMark
    fields = ['claim']
    template_name = 'exammark/raise.html'
    pk_url_kwarg = 'eid'
    
    def get_context_data( self, **kwargs ):
        context = super(RaiseCrib,self).get_context_data(**kwargs)
        e = self.object
        exam = get_or_none( Exam, pk = e.exam_id )
        context[ "is_auth" ] = (who_auth( self.request ) == e.rollno) and (e.raise_time == None) and (exam.is_cribs_active == True)
        context[ "e" ] = e
        return context

    def form_valid(self,form):
        try:
            u = who_auth( self.request )
            s = self.object
            if  u != s.rollno: raise Exception( f'[Attack] wrong student is modifying a crib {s.rollno} != {u}' )
            return super().form_valid(form)
        except Exception as e:
            logq.error( '{}!'.format(e) )
            form.add_error( None, '{}!'.format(e) )
            return redirect( reverse( 'index' ) )

    def get_success_url(self):
        e = self.object
        e.raise_time = timezone.now()
        cribs = ExamMark.objects.filter( Q(q = e.q)&(~Q(raise_time = None))&Q(exam_id = e.exam_id) )
        e.crib_num = len(cribs)+1
        e.save()
        messages.success(self.request,f'Cribs raised by {e.rollno} for score id {e.id} !')
        logq.info( f'Cribs raised by {e.rollno} for score id {e.id} !' )
        return reverse( "index" )


class RaiseCrib2(UpdateView):
    model = ExamMark
    fields = ['claim2']
    template_name = 'exammark/raise2.html'
    pk_url_kwarg = 'eid'
    
    def get_context_data( self, **kwargs ):
        context = super(RaiseCrib2,self).get_context_data(**kwargs)
        e = self.object
        old_cribs = ExamMark.objects.filter( (~Q(raise_time2 = None))&Q(rollno = e.rollno) )
        exam = get_or_none( Exam, pk = e.exam_id )
        context[ "is_auth" ] = (len(old_cribs) < 4) and (who_auth( self.request ) == e.rollno) and (e.response_time != None) and (e.raise_time2 == None) and (exam.is_cribs_active == True)
        context[ "e" ] = e
        return context

    def form_valid(self,form):
        try:
            u = who_auth( self.request )
            s = self.object
            if  u != s.rollno: raise Exception( f'[Attack] wrong student is modifying a crib {s.rollno} != {u}' )
            return super().form_valid(form)
        except Exception as e:
            logq.error( '{}!'.format(e) )
            form.add_error( None, '{}!'.format(e) )
            return redirect( reverse( 'index' ) )

    def get_success_url(self):
        e = self.object
        e.raise_time2 = timezone.now()
        e.save()
        messages.success(self.request,f'Cribs raised by {e.rollno} for score id {e.id} !')
        logq.info( f'Cribs raised by {e.rollno} for score id {e.id} !' )
        return reverse( "index" )

class ResponseCrib(UpdateView):
    model = ExamMark
    fields = ['crib_marks','response']
    template_name = 'exammark/response.html'
    pk_url_kwarg = 'eid'
    
    def get_context_data( self, **kwargs ):
        context = super(ResponseCrib,self).get_context_data(**kwargs)
        link = self.kwargs['link']
        e = self.object
        exam = get_or_none( Exam, pk = e.exam_id )
        context[ "is_auth" ] = ( link == exam.link ) and (exam.is_cribs_active == True)
        context[ "e" ] = e
        context[ "appeal" ] = False
        context[ "link" ] = link
        return context

    def form_valid(self,form):
        try:
            link = self.kwargs['link']
            e = self.object
            exam = get_or_none( Exam, pk = e.exam_id )
            is_auth = ( link == exam.link ) and (exam.is_cribs_active == True)
            if  not is_auth : raise Exception( f'[Attack] Bad crib response link!' )
            return super().form_valid(form)
        except Exception as e:
            logq.error( '{}!'.format(e) )
            form.add_error( None, '{}!'.format(e) )
            return redirect( reverse( 'index' ) )

        
    def get_success_url(self):
        e = self.object
        e.is_accepted   = True
        e.response_time = timezone.now()
        e.save()
        exam = get_or_none( Exam, pk = e.exam_id )
        logq.info( 'Crib for score id ' + str(e.id) + ' is accepted.' )
        # return redirect( reverse('index') )
        return reverse('cribs', kwargs={'eid':e.exam_id,'qid':e.q,'link':exam.link})

class ResponseCrib2(UpdateView):
    model = ExamMark
    fields = ['crib_marks2','response2']
    template_name = 'exammark/response.html'
    pk_url_kwarg = 'eid'
    
    def get_context_data( self, **kwargs ):
        context = super(ResponseCrib2,self).get_context_data(**kwargs)
        e = self.object
        exam = get_or_none( Exam, pk = e.exam_id )
        context[ "is_auth" ] = ( (who_auth( self.request ) == 'prof') ) and (exam.is_cribs_active == True)
        context[ "appeal"  ] = True
        context[ "e"       ] = e
        return context

    def form_valid(self,form):
        try:
            e = self.object
            exam = get_or_none( Exam, pk = e.exam_id )
            is_auth = ( (who_auth( self.request ) == 'prof') ) and (exam.is_cribs_active == True)
            if  not is_auth : raise Exception( f'[Attack] Bad crib response link!' )
            return super().form_valid(form)
        except Exception as e:
            logq.error( '{}!'.format(e) )
            form.add_error( None, '{}!'.format(e) )
            return redirect( reverse( 'index' ) )
        
    def get_success_url(self):
        e = self.object
        e.is_accepted2   = True
        e.response_time2 = timezone.now()
        e.save()
        exam = get_or_none( Exam, pk = e.exam_id )
        logq.info( 'Crib2 for score id ' + str(e.id) + ' is accepted.' )
        return reverse('cribs2', kwargs={'eid':e.exam_id})


def reject_crib(request, eid, link, reason):
    e = get_or_none( ExamMark, pk = eid )
    if (e == None):
        return HttpResponse( 'Incorrect crib!' )
    exam = get_or_none( Exam, pk = e.exam_id )
    if exam.link != link:
        return HttpResponse( 'Bad URL!' ) 
    e.is_accepted   = False
    e.response_time = timezone.now()
    e.response = reason
    e.save()
    messages.success(request,f'Cribs for score id {e.id} is rejected!')
    logq.info( f'Cribs for score id {e.id} is rejected!' )
    return redirect( reverse('cribs', kwargs={'eid':e.exam_id,'qid':e.q,'link':exam.link}) )


def reject_crib2(request, eid):
    if who_auth(request) != 'prof': return HttpResponse( 'Incorrect login!' )    
    e = get_or_none( ExamMark, pk = eid )
    if (e == None):
        return HttpResponse( 'Incorrect crib!' )
    e.is_accepted2   = False
    e.response_time2 = timezone.now()
    e.save()
    messages.success(request,f'Appeal for scode id {e.id} is rejected!')
    logq.info( f'Appeal for scode id {e.id} is rejected!' )
    return redirect( reverse('cribs2', kwargs={'eid':e.exam_id}) )

def read_absents(student):
    absents = {}
    for course in student.course.split(':'): absents[course] = []
    if student.absent:
        for absent in student.absent.split(','):
            ab = absent.split(':')
            if len(ab) == 2 and ab[0] in student.course:
                course = ab[0]
                exam   = ab[1]
                absents[course].append(exam)
    return absents

@transaction.atomic
def compute_total_scores(request):
    if who_auth(request) != 'prof': return HttpResponse( 'Incorrect login!' )
    student_list = StudentInfo.objects.order_by('rollno')
    do_not_compute_for_courses = ['CS213']
    do_not_compute_for_students = ['24B1004', '24B0989', '210050102', '24B0956', '24B1001', '24B1087', '24B0910', '24B1030', '23B1054', '24B1050', '24B1053', '24B1017']
    for student in student_list:
        if student.rollno in do_not_compute_for_students: continue
        absents = read_absents(student)
        scores = ""
        for c in student.course.split(':'):
            if c in do_not_compute_for_courses: continue 
            exams = Exam.objects.filter( Q(course = c) )
            missed   = 0.0
            weighted = 0.0
            calculation = []
            if exams:
                for exam in exams:
                    if exam.name in absents[c]:
                        missed += float(exam.weight)
                    total = 0.0
                    for qid in range(1,exam.num_q+1):
                        score = get_or_none( ExamMark, exam_id = exam.id, rollno=student.rollno, q=qid )
                        marks,_ = get_score(score)
                        total += float(marks)
                    exam_score = float(total)*float(exam.weight)/float(exam.total)
                    weighted += exam_score
                    calculation.append(f"({exam.total}/{exam.weight}){total}")
            calculation = "+".join(calculation)
            if missed > 0:
                weighted = weighted*100/(100-missed)
                calculation = f"100/(100-{missed})({calculation})"
            weighted = round(weighted, 2)
            scores += f"{c}:{calculation}={weighted}%,"
        student.total_scores = scores
        student.save()
    return redirect( reverse( 'index' ) )


# def raise_crib(request, eid):
#     u = who_auth(request)
#     e = get_or_none( ExamMark, pk = eid )
#     if (e == None) or (e.rollno != u):
#         return HttpResponse( 'Incorrect login!' )
#     e.raise_time = timezone.now()
#     e.save()
#     messages.success(request,'Cribs raised by '+e.rollno+' for score id '+ eid +'!')
#     logq.info( 'Cribs raised by '+e.rollno+' for score id '+ eid +'!' )
#     return redirect( reverse( 'index' ) )
