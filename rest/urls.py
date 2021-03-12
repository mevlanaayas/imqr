# -*- coding: utf-8 -*-
from django.urls import path

from rest import views

app_name = 'rest'
urlpatterns = [
    path('', views.index, name='index'),
    path('library', views.library, name='library'),
    path('<uuid:file_id>/', views.detail, name='detail'),
    path('<uuid:file_id>/delete', views.delete, name='delete'),
    path('upload', views.upload, name='upload'),
]
