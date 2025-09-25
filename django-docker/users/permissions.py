from rest_framework.permissions import BasePermission  # type:ignore
from .models import Roles


class IsCompany(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Roles.COMPANY
        )


class IsCandidate(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == Roles.CANDIDATE
        )
