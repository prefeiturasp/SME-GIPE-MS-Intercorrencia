from rest_framework import serializers
from intercorrencias.models.intercorrencia import Intercorrencia


class UUIDInputSerializer(serializers.Serializer):
    uuid = serializers.UUIDField()

    def is_valid(self, raise_exception=False):
        valid = super().is_valid(raise_exception=False)

        if not valid:
            first_field, first_error_list = next(iter(self.errors.items()))
            message = first_error_list[0] if isinstance(first_error_list, list) else str(first_error_list)

            self._errors = {"detail": f"{first_field}: {message}"}

            if raise_exception:
                raise serializers.ValidationError(self._errors)

        return valid


class VerifyIntercorrenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intercorrencia
        fields = "__all__"