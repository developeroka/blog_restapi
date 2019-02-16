from django.contrib.admin import AdminSite
from rest import models
from django.contrib.auth.models import User
from django.contrib import admin


class BlogAdmin(admin.ModelAdmin):
    list_display = ('post_title', 'post_author', )
    search_fields = ['post_title', 'post_content', ]
    list_filter = ('post_category', )

    def get_queryset(self, request):
        return models.BlogPost.objects.filter(post_author=request.user) | \
               models.BlogPost.objects.filter(post_privacy='public')


class PostCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_title', )
    search_fields = ['category_title', ]
    list_filter = ('category_name', )


class MyAdminSite(AdminSite):
    site_header = 'Fitro administration'


admin_site = MyAdminSite(name='admin')
admin_site.register(models.BlogPost, BlogAdmin)
admin_site.register(models.PostCategory, PostCategoryAdmin)
admin_site.register(models.ApiToken)
admin_site.register(User)

