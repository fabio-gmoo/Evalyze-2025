from django.urls import path  # type: ignore
from .views import RegisterCompanyView, RegisterCandidateView, MeView
from .views_auth import RoleTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView  # type: ignore

urlpatterns = [
    path(
        "auth/register/company/", RegisterCompanyView.as_view(), name="register_company"
    ),
    path(
        "auth/register/candidate/",
        RegisterCandidateView.as_view(),
        name="register_candidate",
    ),
    path("auth/login/", RoleTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
]
