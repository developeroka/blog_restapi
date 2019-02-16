from django.urls import path
from rest import views


urlpatterns = [
    path('api', views.RestApi.api),
    path('', views.UserActivity.register)
]
