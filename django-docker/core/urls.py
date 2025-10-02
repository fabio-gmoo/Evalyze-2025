# core/urls.py  (o el urls.py raíz del proyecto)
from django.contrib import admin  # type: ignore
from django.urls import path, include  # type: ignore

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("jobs.urls")),
    path("api/auth/", include("users.urls")),
]
