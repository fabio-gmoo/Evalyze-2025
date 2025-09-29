# Create your views here.rom rest_framework import generics, permissions
from rest_framework.views import APIView  # type: ignore
from rest_framework.response import Response  # type: ignore
from rest_framework import generics, permissions  # type: ignore
from django.contrib.auth import get_user_model  # type:ignore
from .serializers import (  # type: ignore
    RegisterCompanySerializer,
    RegisterCandidateSerializer,
    UserSerializer,
)
from rest_framework.permissions import IsAuthenticated  # type: ignore

User = get_user_model()


class RegisterCompanyView(generics.CreateAPIView):
    serializer_class = RegisterCompanySerializer
    permission_classes = [permissions.AllowAny]


class RegisterCandidateView(generics.CreateAPIView):
    serializer_class = RegisterCandidateSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)
