from django.contrib import admin
from django.urls import path, include

from ram_redis_app.urls import urlpatterns as ram_app_urls


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(ram_app_urls)),
]
