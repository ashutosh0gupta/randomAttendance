from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.generic.edit import FormView, View, CreateView, UpdateView
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from account.forms import UserLoginForm
from account.models import *
from django.urls import reverse_lazy, reverse
from datetime import datetime
year = datetime.now().year

test_mode = True

# class UserLoginView(FormView):
class UserLoginView(FormView):
    form_class = UserLoginForm
    template_name = 'account/login.1.html'
    success_url = reverse_lazy('index')

    def get(self, request, *args, **kwargs):
        next_ = request.GET.get('next',self.success_url)
        if next_=='':
            next_ =  self.success_url
        if request.user.is_authenticated:
            return redirect(next_)

        return render(request,self.template_name,{'form':self.form_class})


    def post(self,request, *args, **kwargs):
        form = self.form_class(request.POST)
        next_ = request.POST.get('next', self.success_url)

        if next_ == '':
            next_ = self.success_url
        #todo : workout what is_valid does
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            print(user)
        else:
            user = None

        if user is not None:
            # print(hasattr(user, 'ldap_user'))
            login(request,user)
            return redirect(self.success_url)
        else:
            # print(form.errors.as_json)
            messages.error(request, 'Unknown user / Authentication failed for {}'.format(username))
            return redirect(reverse('logout'))

    def who_is(self,user):
        return user.groups.filter(name__contains='fac').exists()

    def is_faculty(self,user):
        return user.groups.filter(name__contains='fac').exists()

    def is_staff(self,user):
        # return  user.groups.filter(name__conatins="webteam").exists() or user.groups.filter(name__contains='staff').exists()
        return  user.groups.filter(name__contains='staff').exists()


    def is_webteam(self,user):
        return user.groups.filter(name__contains="webteam").exists()

    # def is_student(self,user):
    #     # print(year-2000)
    #     pg = user.groups.filter(name__contains='pg').exists()
    #     ug = user.groups.filter(name__contains='ug').exists()
    #     phd =user.groups.filter(name__contains='rs').exists()
    #     # print(user.groups.filter(name__contains='pg'))
    #     return pg or ug or phd
    
    def __init__(self):
        print('Login View Loaded')
        return

    
# @login_required(login_url=reverse_lazy('login'))
class UserLogoutView(View):
    def post(self, request, *args, **kwargs):
        if request.user:
            print('Currently post logged in {}'.format(request.user))
            logout(request)
        return redirect('logout')

    def get(self, request, *args, **kwargs):
        if request.user:
            print('Currently logged in {}'.format(request.user))
            logout(request)
        return redirect('login')

    def __init__(self):
        print('logout')


@login_required(login_url=reverse_lazy('login'))
def index(request):
    return render(request, 'account/success.html')
