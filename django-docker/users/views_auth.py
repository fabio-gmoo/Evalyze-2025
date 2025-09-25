from rest_framework_simplejwt.views import TokenObtainPairView  # type: ignore
from .token import RoleTokenObtainPairSerializer  # type: ignore


class RoleTokenObtainPairView(TokenObtainPairView):
    serializer_class = RoleTokenObtainPairSerializer
