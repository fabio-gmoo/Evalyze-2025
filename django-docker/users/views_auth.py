from rest_framework.permissions import AllowAny  # type: ignore
from rest_framework_simplejwt.views import TokenObtainPairView  # type: ignore
from .token import RoleTokenObtainPairSerializer  # type: ignore


class RoleTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = RoleTokenObtainPairSerializer
