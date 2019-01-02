from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('all/', views.all_status, name='all'),
    path('<int:student_id>/', views.status, name='status'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
