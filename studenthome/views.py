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
from django.conf import settings
from django.utils import timezone

import logging

import csv
import os
import shutil
import datetime
import random
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
            # test situation where we do not care of ldap authenticaiton
            return u.username
    except AttributeError:
        return str(u.username)

def who_auth(request):
    u = request.user
    if u.is_anonymous:
        if settings.DEBUG:
            return '190050057'
            # return '174050004'
            # return '170050004'
            # return '170050053'
            # return "prof"
        return None
    if u.username == "akg" or u.username == "omkarvtuppe" or u.username == "ivarnam" or u.username == "krishnas":
        return "prof"
    # if studentinfo is not found, the student is not registered in the course.
    s = get_or_none( StudentInfo, username = u.username )
    if s == None:
        rollno = get_user_rollno( u )
        # print('I am here:' + rollno)
        s = get_or_none( StudentInfo, pk = rollno )
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
    if p == "prof":
        if s.mode == "QUIZ":
            logq.info( 'prof Quiz status request' )
            q = get_or_none( Question, pk=find_first_active_question() )
            # question on the screen
            if( q != None ):
                context["q"] = clean_latex( q.q) # LatexNodes2Text().latex_to_text( q.q )
            else:
                context["q"] = ""
            context[ "students" ] = StudentInfo.objects.all()
            response = render( request, 'studenthome/quiz.html', context.flatten() )
            logq.info( 'prof Quiz status rendered' )
            return response # render( request, 'studenthome/quiz.html', context.flatten() )
        else:
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
        return redirect( reverse('answer', kwargs={'ansid':sa.pk}) )
    else:
        return HttpResponse( "Quiz is not running!! Refresh to check if it is running now!" )
    

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
    logq.info( 'Import ran!' )
    return HttpResponse(imported+deleted)

    
# def question(request):
#     if is_student(request):
#         return student_attempt(attempt)
#     if is_prof(request):
#         return show_question(attempt)
#     return HttpResponse( 'No login or unregistered user!' )        

#--------------------------------------------------------------------
# question creation and management

q_fields = ['q']
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
    fields= ['q','trues','falses'] #q_fields
    # fields= ['q','trues','falses','fillCode','checkCode']
    template_name = 'studenthome/qcreate.html'

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
            d.save()

            # view options on the command line
            for op_name in op_fields:
                op = d._meta.get_field(op_name)
                op_str = op.value_from_object(d)
                if op_str :
                    uni_op = clean_latex( op_str ) #LatexNodes2Text().latex_to_text(op_str)
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
    template_name = 'studenthome/editq.html'
    pk_url_kwarg = 'qid'
    
    def get_context_data( self, **kwargs ):
        context = super(EditQuestion,self).get_context_data(**kwargs)
        context[ "is_auth" ] = (who_auth( self.request ) == "prof")
        return context

    def get_success_url(self):
        q = self.object
        logq.info( 'Question ' + str(q.id) + ' edited.' )
        return reverse( "createq" )

def deleteq(request, qid):
    u = who_auth(request)
    if u != 'prof':
        return HttpResponse( 'Incorrect login!' )
    q = get_or_none( Question, pk = int(qid) )
    StudentAnswers.objects.filter(q=qid).delete()
    
    if q:
        if q.first_activation_time != None:
            # if quiz has been attempted
            sys = get_sys_state()
            sys.num_attendance = sys.num_attendance - 1
            sys.save()
        messages.success(request,'Question '+str(q.id)+' deleted!')
        q.delete()
        logq.info( 'Question ' + str(qid) + ' deleted.' )
 
    # return HttpResponse( 'Done!' )
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
    return render( request, 'studenthome/viewq.html', context.flatten() )

    
def get_sys_state():
    s, created = SystemState.objects.get_or_create(pk = 1)
    return s

def get_active_q( i ):
    sys = get_sys_state()
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
        print(iid)
        print(i)
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


#-----------------------------------------------------------------------------
# Running quiz

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
    #
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
    
    for s in ss:
        statuses = []
        for q in qs:
            sa = get_or_none( StudentAnswers, rollno=s.rollno, q=q.pk )
            # if sa == None:
            #     #
            #     # expected to occur rarely. Only if a student is added later
            #     #
            #     ops = get_active_options( q )                
            #     op = random.sample( ops, 4 )
            #     sa = StudentAnswers.objects.create(rollno=s.rollno, q=q.pk)
            #     sa.op1 = op[0]
            #     sa.op2 = op[1]
            #     sa.op3 = op[2]
            #     sa.op4 = op[3]
            #     sa.save() # todo: save in one shot (ineffcient now!)
            statuses.append( get_answer_status( sa ) )
        # only needs db change if multiple quizzes were executed
        status = quiz_status( statuses )
        if status != s.curr_status:
            s.curr_status = status
            s.save()
            
        
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
    if len(student_list) > 3:
        #todo: remove this loop
        s_list = []
        for s in student_list:
            s_list.append(s)
        s1,s2,s3 = random.sample( s_list, 3 )
    else:
        if len(student_list) > 2:
            s3 = student_list[2]
        if len(student_list) > 1:
            s2 = student_list[1]            
        if len(student_list) > 0:
            s1 = student_list[0]
    context = RequestContext(request)
    context.push( {'s1': s1, 's2': s2, 's3': s3 } )
    logq.info( 'Quiz for Question ' + str(sys.activeq1) + str(sys.activeq2) + str(sys.activeq3) +str(sys.activeq4) + ' is stopped.' )

    return render( request, 'studenthome/results.html', context.flatten() )

#------------------------------------------------------------------------------
# Student answering quiz

def calculate_student_status(s):
    statuses = []
    for i in range(1,5):
        qid = get_active_q( i )
        if qid > 0:
            sa = get_or_none(StudentAnswers,rollno=s.rollno, q=qid)
            statuses.append( get_answer_status( sa ) )
    return quiz_status( statuses )
            
class StudentResponse(UpdateView):
    model = StudentAnswers
    fields = ['ans1','ans2','ans3','ans4']
    template_name = 'studenthome/answer.html'
    pk_url_kwarg = 'ansid'
    
    def get_context_data( self, **kwargs ):
        context = super(StudentResponse,self).get_context_data(**kwargs)
        sa = self.object
        
        # identifiy the next and previous quiz id 
        idx = 0
        nxt = None
        prv = None
        q_num = 1
        for i in range(1,5):
            qid = get_active_q( i )
            if idx > 0 and qid > 0:
                nxt = get_or_none(StudentAnswers,rollno=sa.rollno, q=qid)
                break
            if idx == 0 and qid > 0 and qid != sa.q:
                prv = get_or_none(StudentAnswers,rollno=sa.rollno, q=qid)
                q_num = q_num + 1
            if qid == sa.q:
                idx = i
        
        get_sys_state()
        # populate context
        q = get_or_none( Question, pk=sa.q )
        sys = get_sys_state()
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
        context["q_num"] = q_num
        context["prev"] = prv # link to the previous question
        context["next"] = nxt # link to the next question

        return context

    def form_valid(self,form):
        try:
            sa = None
            sa = self.object
            logq.info( str(sa.rollno) + ' submitting.' )
            if who_auth( self.request ) != sa.rollno:
                user_id = who_auth( self.request )
                raise Exception( '[Attack] wrong student is trying to submit '+ str(user_id) + '!=' + str(sa.rollno) )
            sys = get_sys_state()
            if sys.mode != 'QUIZ': 
                raise Exception( str(sa.rollno) + ' submitting, while quiz is closed.' )
            if sys.activeq1 != sa.q and sys.activeq2 != sa.q and sys.activeq3 != sa.q and sys.activeq4 != sa.q:
                raise Exception( str(sa.rollno) + ' wrong question being answered.' )
            if sa.answer_time :
                raise Exception( str(sa.rollno) + ' answer is already submitted!' )

            # saving the options
            response = super().form_valid(form)

            sa = self.object
            # record student response details
            sa.answer_time = timezone.now() 
            sa.user_agent = self.request.headers['User-Agent'] #+'::'+self.request.headers['Origin']
            sa.is_correct,c_count = is_answer_correct( sa )
            sa.correct_count = c_count
            sa.save()
            logq.info( str(sa.rollno) + ' answer-saved-'+str(c_count)+'.' )

            # update student
            s = get_or_none(StudentInfo, pk=sa.rollno)
            s.curr_status = calculate_student_status(s)
            s.save()
            
            logq.info( str(sa.rollno) + ' answered-' + str(sa.q) )
            return response
        except Exception as e:
            # No timing is saved
            logq.error( '{}!'.format(e) )
            form.add_error( None, '{}!'.format(e) )
            # messages.error(self.request,'{}!'.format(e))
            return redirect( reverse( 'index' ) )
            # return super().form_invalid(form)

    def get_success_url(self):
        return reverse('answer', kwargs={'ansid':self.object.id})
        # return reverse( "index" )


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
        devs = set()
        corrects[student.rollno] = 0
        three_corrects[student.rollno] = 0
        wrongs[student.rollno] = 0
        for sa in attendances:
            b,corr_count = is_answer_correct( sa )
            dt = sa.answer_time.strftime("%m-%d")
            devs.add( sa.user_agent )
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
    reverse_dev_map = dict()
    for rollno,devs in device_map.items():
        for dev in devs:
            if dev in reverse_dev_map:
                reverse_dev_map[dev].add(rollno)
            else:
                reverse_dev_map[dev] = { rollno }                
                
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

