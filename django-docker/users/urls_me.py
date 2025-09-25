from django.urls import path  # type: ignore
from .views import MeView

urlpatterns = [path("", MeView.as_view(), name="me")]
