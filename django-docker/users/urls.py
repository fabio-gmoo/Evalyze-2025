from django.urls import path  # type: ignore
from .views import RegisterCompanyView, RegisterCandidateView, MeView
from .views_auth import RoleTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView  # type: ignore

urlpatterns = [
    path("register/company/", RegisterCompanyView.as_view(), name="register_company"),
    path(
        "register/candidate/",
        RegisterCandidateView.as_view(),
        name="register_candidate",
    ),
    path("login/", RoleTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
]
