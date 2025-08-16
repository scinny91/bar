
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('bar.urls')),
    path('silk/', include('silk.urls', namespace='silk'))
]
