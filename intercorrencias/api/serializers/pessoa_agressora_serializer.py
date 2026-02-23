from rest_framework import serializers
from intercorrencias.models.pessoa_agressora import PessoaAgressora


class PessoaAgressoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = PessoaAgressora
        fields = ["id","uuid", "nome", "idade",]
        read_only_fields = ["id", "uuid"]

    def validate_nome(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("O nome não pode estar em branco")
        return value.strip()

    def validate_idade(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("A idade deve ser um número positivo.")
        return value
    
    def is_valid(self, raise_exception=False):

        valid = super().is_valid(raise_exception=False)
        if not valid:
            first_field, first_error_list = next(iter(self.errors.items()))
            message = (
                first_error_list[0]
                if isinstance(first_error_list, list)
                else str(first_error_list)
            )

            if isinstance(self._errors, dict) and "detail" in self._errors:
                error_dict = self._errors
            else:
                error_dict = {"detail": f"{first_field}: {message}"}

            self._errors = error_dict

            if raise_exception:
                raise serializers.ValidationError(self._errors)

        return valid
    