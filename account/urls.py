# from django.conf.urls import urls
from django.shortcuts import render
from django.urls import path
from account.views import UserLoginView, UserLogoutView
from . import views

urlpatterns = [
    # path('',views.index,name='profile-index'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('success/',views.index,name='success')
]
