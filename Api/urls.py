from rest.admin import admin_site
from django.urls import include, path

urlpatterns = [
    path('admin/', admin_site.urls),
    path('rest/', include('rest.urls')),
    path(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
