from rest_framework_simplejwt.serializers import TokenObtainPairSerializer  # type: ignore
from rest_framework import serializers  # type: ignore


class RoleTokenObtainPairSerializer(TokenObtainPairSerializer):
    role = serializers.CharField(required=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # claims extra (útiles en el front)
        token["email"] = user.email
        token["role"] = user.role
        token["name"] = user.name
        return token

    def validate(self, attrs):
        selected_role = attrs.get("role")

        # SUPER ya agrega 'access' y 'refresh'
        data = super().validate(attrs)

        if self.user.role != selected_role:
            raise serializers.ValidationError(
                {
                    "role": f"Este usuario no tiene rol de '{selected_role}'. Tiene rol de '{self.user.role}'."
                }
            )

        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "role": self.user.role,
            "name": self.user.name,
        }
        return data
