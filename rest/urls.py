from django.conf.urls import url
from django.urls import path
from rest import views


urlpatterns = [
    path('api', views.RestApi.api),
    path('register', views.UserActivity.register),
    path('login', views.UserActivity.login)
]
