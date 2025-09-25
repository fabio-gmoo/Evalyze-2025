from django.urls import path  # type: ignore
from .views import RegisterCompanyView, RegisterCandidateView, MeView

urlpatterns = [
    path("register/company/", RegisterCompanyView.as_view(), name="register_company"),
    path(
        "register/candidate/",
        RegisterCandidateView.as_view(),
        name="register_candidate",
    ),
    path("me/", MeView.as_view(), name="me"),
]
