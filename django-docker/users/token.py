from rest_framework_simplejwt.serializers import TokenObtainPairSerializer  # type: ignore


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        # Si quieres company_id para empresas:
        if hasattr(user, "company_profile"):
            token["company_id"] = user.company_profile.id
        return token
