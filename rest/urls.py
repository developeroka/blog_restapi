from django.urls import path
from rest import views


urlpatterns = [
    path('api', views.ApiEndpoints.api),
    path('api/category', views.ApiEndpoints.categories),
    path('register', views.UserActivity.register),
    path('login', views.UserActivity.login),
    path('api/getpostbyid', views.ApiEndpoints.get_post_by_id),
    path('api/getpostsbylength', views.ApiEndpoints.get_posts_by_length),
    path('api/deletepostbyid', views.ApiEndpoints.delete_post_by_id)
]
