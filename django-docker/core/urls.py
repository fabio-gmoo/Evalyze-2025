# core/urls.py  (o el urls.py raíz del proyecto)
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("jobs.urls")),
]
