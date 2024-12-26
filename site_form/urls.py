from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_and_analyze, name='upload_file'),
    path('diseases/', views.upload_and_analyze, name='upload_file'),
]
