from rest_framework_simplejwt.serializers import TokenObtainPairSerializer  # type: ignore
from rest_framework import serializers  # type: ignore


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    role = serializers.CharField(required=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # claims extra (útiles en el front)
        token["email"] = user.email
        token["role"] = getattr(user, "role", None)
        return token

    def validate(self, attrs):
        selected_role = attrs.get("role")

        # SUPER ya agrega 'access' y 'refresh'
        data = super().validate(attrs)

        user_role = getattr(self.user, "role", None)

        if user_role != selected_role:
            raise serializers.ValidationError(
                {
                    "role": f"Este usuario no tiene rol de '{selected_role}'. Tiene rol de '{user_role}'."
                }
            )

        # añade datos del usuario a la respuesta (opcional)
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "role": getattr(self.user, "role", None),
        }
        return data
