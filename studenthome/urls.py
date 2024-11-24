from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('all/', views.all_status, name='all'),
    path('import/', views.db_import, name='import'),
    path('createlocal/', views.create_local_users, name='createlocal'),
    re_path(r'^(?P<rollno>\d\d[0-9BDVMbvm]+\d+)/$', views.status, name='status'),
    path('startq/', views.startq, name='startq'),
    path('stopq/', views.stopq, name='stopq'),
    path('createq/', views.CreateQuestion.as_view(), name='createq'),
    re_path(r'^viewq/(?P<qid>\d+)/', views.viewq, name='viewq'),
    re_path(r'^editq/(?P<qid>\d+)/', views.EditQuestion.as_view(), name='editq'),    
    re_path(r'^deleteq/(?P<qid>\d+)/$', views.deleteq, name='deleteq'),
    re_path(r'^swapq/(?P<qid1>\d+)/(?P<qid2>\d+)/$', views.swapq, name='swapq'),
    re_path(r'^activateq/(?P<iid>\d+)/(?P<qid>\d+)/$', views.activateq, name='activateq'),
    re_path(r'^deactivateq/(?P<iid>\d+)/$', views.deactivateq, name='deactivateq'),    
    re_path(r'^answer/(?P<ansid>\d+)/', views.StudentResponse.as_view(), name='answer'),

    # # Exam data interface
    # path('examc/', views.examc, name='examc'),
    # path('exame/', views.examc, name='exame'),
    # path('examd/', views.examc, name='examd'),

    # # Scores upload interface
    # path('scoreupload/', views.score_upload, name='scoreupload'),
    # path('scorecrib/'  , views.score_crib  , name='scorecrib'),
    # path('scoreedit/'  , views.score_edit  , name='scoreedit'),

    #--------------------
    # Biobreak management
    #--------------------
    re_path('^biobreak/(?P<dayhash>\w+)/', views.AddBioBreak.as_view(), name='biobreak'),
    re_path('^biobreakreturn/(?P<dayhash>\w+)/(?P<rid>\d+)/'  , views.biobreak_return  , name='biobreakreturn'  ),
    re_path('^biobreakurgent/(?P<dayhash>\w+)/(?P<rid>\d+)/'  , views.biobreak_urgent  , name='biobreakurgent'  ),
    re_path('^biobreakwithdraw/(?P<dayhash>\w+)/(?P<rid>\d+)/', views.biobreak_withdraw, name='biobreakwithdraw'),

    #----------------------
    # Exam rooms management
    #----------------------
    path('createexamroom/', views.CreateExamRoom.as_view(), name='createexamroom'),
    re_path(r'^editexamroom/(?P<rid>\d+)/', views.EditExamRoom.as_view(), name='editexamroom'),    
    re_path(r'^deleteqexamroom/(?P<rid>\d+)/$', views.delete_exam_room, name='deleteexamroom'),
    re_path('allocateseats/(?P<cid>\w+)', views.seating, name='allocateseats'),

    #----------------------
    # Exam management
    #----------------------
    path('createexam/', views.CreateExam.as_view(), name='createexam'),
    re_path(r'^editexam/(?P<rid>\w+)/', views.EditExam.as_view(), name='editexam' ),    
    re_path(r'^deleteexam/(?P<rid>\w+)/$', views.delete_exam,   name='deleteexam' ),
    re_path(r'^enablecrib/(?P<rid>\w+)/$', views.enable_crib,   name='enablecrib' ),
    re_path(r'^disablecrib/(?P<rid>\w+)/$', views.disable_crib, name='disablecrib'),
    
    #----------------------
    # Crib management
    #----------------------
    re_path('raisecrib/(?P<eid>\w+)', views.raise_crib, name='raisecrib'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


    # re_path(r'^(?P<rollno>[0-9DV]+)/$', views.status, name='status'),
