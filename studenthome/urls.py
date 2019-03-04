from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('never/', views.never, name='never'),
    path('all/', views.all_status, name='all'),
    path('import/', views.db_import, name='import'),
    re_path(r'^(?P<rollno>\d\d[0-9D]\d+)/$', views.status, name='status'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
