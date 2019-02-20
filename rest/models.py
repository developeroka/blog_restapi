from django.db import models
from django.contrib.auth.models import User


class PostCategory(models.Model):
    category_title = models.CharField(max_length=100)
    category_name = models.CharField(max_length=100)
    parent_id = models.ManyToManyField('self', blank=True)

    def __str__(self):
        return str(self.id) + '-' + self.category_title


class BlogPost(models.Model):
    Public = 'public'
    Private = 'private'
    privacy_choices = ((Public, 'public'),
                       (Private, 'private'))
    post_title = models.CharField(max_length=100)
    post_content = models.CharField(max_length=1000)
    post_author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    post_category = models.ForeignKey(PostCategory, on_delete=models.CASCADE)
    post_privacy = models.CharField(max_length=50, null=True, default='public', choices=privacy_choices,)

    def __str__(self):
        return str(self.id) + '-' + self.post_title


class ApiToken(models.Model):
    token_content = models.CharField(max_length=256)
    token_expired = models.DateTimeField()
    token_clientId = models.CharField(max_length=500)
    token_user = models.ForeignKey(User, on_delete=models.CASCADE)
