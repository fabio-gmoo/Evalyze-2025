from rest_framework_simplejwt.serializers import TokenObtainPairSerializer  # type: ignore


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        t = super().get_token(user)
        t["sub"] = str(user.id)
        t["email"] = user.email
        t["role"] = getattr(user, "role", None)
        # si aplica:
        # t['company_id'] = user.companyprofile_id
        return t
