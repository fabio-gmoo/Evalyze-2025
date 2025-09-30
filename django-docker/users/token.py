from rest_framework_simplejwt.serializers import TokenObtainPairSerializer  # type: ignore


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # claims extra (útiles en el front)
        token["email"] = user.email
        token["role"] = getattr(user, "role", None)
        return token

    def validate(self, attrs):
        # SUPER ya agrega 'access' y 'refresh'
        data = super().validate(attrs)
        # añade datos del usuario a la respuesta (opcional)
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "role": getattr(self.user, "role", None),
        }
        return data
