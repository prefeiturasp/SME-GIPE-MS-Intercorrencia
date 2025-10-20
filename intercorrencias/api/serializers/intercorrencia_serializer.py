from rest_framework import serializers
from intercorrencias.services import unidades_service
from intercorrencias.models.intercorrencia import Intercorrencia


class IntercorrenciaSerializer(serializers.ModelSerializer):
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_extra = serializers.SerializerMethodField()

    def get_status_extra(self, obj):
        return obj.STATUS_EXTRA_LABELS.get(obj.status)

    class Meta:
        model = Intercorrencia
        read_only_fields = ("user_username", "uuid", "criado_em", "atualizado_em")
        fields = (
            "id", "uuid", "data_ocorrencia",
            "unidade_codigo_eol", "dre_codigo_eol",
            "sobre_furto_roubo_invasao_depredacao",
            "user_username", "criado_em", "atualizado_em",
            "status_display", "status_extra"
        )

    def validate(self, attrs):
        """
        Validação cruzada opcional chamando o serviço de Unidades:
        - unidade existe?
        - dre existe?
        - a DRE informada corresponde à DRE da unidade?
        - A unidade pertence ao usuário?
        """
        codigo_unidade = attrs.get("unidade_codigo_eol")
        codigo_dre = attrs.get("dre_codigo_eol")
        request = self.context.get("request")

        try:
            u = unidades_service.get_unidade(codigo_unidade)
        except unidades_service.ExternalServiceError as e:
            raise serializers.ValidationError({"detail": str(e)})

        if not u or u.get("codigo_eol") != codigo_unidade:
            raise serializers.ValidationError({"detail": "Unidade não encontrada."})

        dre_da_unidade = u.get("dre_codigo_eol") or u.get("dre", {}).get("codigo_eol")
        if codigo_dre and dre_da_unidade and (codigo_dre != dre_da_unidade):
            raise serializers.ValidationError({"detail": "DRE informada não corresponde à DRE da unidade."})

        user_unidade = getattr(request.user, "unidade_codigo_eol", None)
        if not user_unidade or user_unidade not in (codigo_unidade, codigo_dre):
            raise serializers.ValidationError({"detail": "A unidade não pertence ao usuário autenticado."})

        return attrs


class IntercorrenciaSecaoInicialSerializer(IntercorrenciaSerializer):
    """Serializer para a seção inicial - Diretor"""

    class Meta:
        model = Intercorrencia
        fields = (
            "uuid", "data_ocorrencia", "unidade_codigo_eol", "dre_codigo_eol",
            "sobre_furto_roubo_invasao_depredacao", "status_display", "status_extra"
        )
        read_only_fields = ("uuid", "status_display")

    def validate(self, attrs):
        return super().validate(attrs)


class IntercorrenciaFurtoRouboSerializer(IntercorrenciaSerializer):
    """Serializer para furto/roubo/invasão/depredação - Diretor"""

    class Meta:
        model = Intercorrencia
        fields = (
            "uuid", "tipos_ocorrencia", "descricao_ocorrencia", "smart_sampa_situacao",
            "status_display", "status_extra"
        )
        read_only_fields = ("uuid",)

    def validate(self, attrs):
        instance = self.instance

        if instance and not instance.sobre_furto_roubo_invasao_depredacao:
            raise serializers.ValidationError(
                "Esta intercorrência não é sobre furto/roubo/invasão/depredação."
            )

        obrigatorios = ["tipos_ocorrencia", "descricao_ocorrencia", "smart_sampa_situacao"]
        for field in obrigatorios:
            if not attrs.get(field) and not (instance and getattr(instance, field)):
                raise serializers.ValidationError({field: "Este campo é obrigatório."})

        return attrs


class IntercorrenciaDiretorCompletoSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem do Diretor"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_extra = serializers.SerializerMethodField()
    smart_sampa_situacao_display = serializers.CharField(
        source='get_smart_sampa_situacao_display', read_only=True
    )

    def get_status_extra(self, obj):
        return obj.STATUS_EXTRA_LABELS.get(obj.status)

    class Meta:
        model = Intercorrencia
        fields = (
            "id", "uuid", "status", "status_display", "status_extra",
            "criado_em", "atualizado_em",
            "data_ocorrencia", "unidade_codigo_eol", "dre_codigo_eol", "user_username",
            "sobre_furto_roubo_invasao_depredacao",
            "tipos_ocorrencia", "descricao_ocorrencia",
            "smart_sampa_situacao", "smart_sampa_situacao_display",
        )
        read_only_fields = ("id", "uuid", "user_username", "criado_em", "atualizado_em")