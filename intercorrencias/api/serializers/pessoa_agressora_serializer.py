from rest_framework import serializers
from intercorrencias.models.pessoa_agressora import PessoaAgressora


class PessoaAgressoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = PessoaAgressora
        fields = [
            "id",
            "uuid",
            "nome",
            "idade",
            "genero",
            "grupo_etnico_racial",
            "etapa_escolar",
            "frequencia_escolar",
            "interacao_ambiente_escolar",
            "nacionalidade",
            "pessoa_com_deficiencia",
        ]
        read_only_fields = ["id", "uuid"]

    def validate_nome(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("O nome não pode estar em branco")
        return value.strip()

    def validate_idade(self, value):
        if value is not None and value <= 0:
            raise serializers.ValidationError("A idade deve ser um número positivo.")
        return value
    
    def validate_genero(self, value):
        if not value:
            raise serializers.ValidationError("O campo gênero é obrigatório.")
        return value

    def validate_grupo_etnico_racial(self, value):
        if not value:
            raise serializers.ValidationError("O campo grupo étnico racial é obrigatório.")
        return value

    def validate_etapa_escolar(self, value):
        if not value:
            raise serializers.ValidationError("A etapa escolar é obrigatória.")
        return value

    def validate_frequencia_escolar(self, value):
        if not value:
            raise serializers.ValidationError("A frequência escolar é obrigatória.")
        return value

    def validate_interacao_ambiente_escolar(self, value):
        if not value:
            raise serializers.ValidationError("A interação no ambiente escolar é obrigatória.")
        return value