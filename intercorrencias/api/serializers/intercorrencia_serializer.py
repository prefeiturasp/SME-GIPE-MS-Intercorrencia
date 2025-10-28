from rest_framework import serializers
from intercorrencias.services import unidades_service
from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia
from intercorrencias.api.serializers.tipo_ocorrencia_serializer import TipoOcorrenciaSerializer


class IntercorrenciaSerializer(serializers.ModelSerializer):
    
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_extra = serializers.SerializerMethodField()

    def get_status_extra(self, obj):
        return obj.STATUS_EXTRA_LABELS.get(obj.status)

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
    
    def is_valid(self, raise_exception=False):
        
        valid = super().is_valid(raise_exception=False)
        if not valid:
            first_field, first_error_list = next(iter(self.errors.items()))
            message = first_error_list[0] if isinstance(first_error_list, list) else str(first_error_list)
            self._errors = {"detail": f"{first_field}: {message}"}

            if raise_exception:
                raise serializers.ValidationError(self._errors)

        return valid


class IntercorrenciaFurtoRouboSerializer(IntercorrenciaSerializer):
    """Serializer para furto/roubo/invasão/depredação - Diretor"""

    tipos_ocorrencia = serializers.SlugRelatedField(
        many=True,
        slug_field="uuid",
        queryset=TipoOcorrencia.objects.all(),
        required=True,
        write_only=True
    )
    tipos_ocorrencia_detalhes = TipoOcorrenciaSerializer(
        many=True,
        read_only=True,
        source="tipos_ocorrencia"
    )
    descricao_ocorrencia = serializers.CharField(required=True, allow_blank=False)
    smart_sampa_situacao = serializers.ChoiceField(
        required=True, 
        allow_blank=False, 
        choices=Intercorrencia.SMART_SAMPA_CHOICES
    )

    class Meta:
        model = Intercorrencia
        fields = (
            "uuid", "tipos_ocorrencia", "tipos_ocorrencia_detalhes", "descricao_ocorrencia", "smart_sampa_situacao",
            "status_display", "status_extra"
        )
        read_only_fields = ("uuid",)

    def validate_tipos_ocorrencia(self, value):
        if not value:
            raise serializers.ValidationError("Este campo é obrigatório e não pode estar vazio.")
        return value

    def validate(self, attrs):
        instance = self.instance
        if instance and not instance.sobre_furto_roubo_invasao_depredacao:
            raise serializers.ValidationError(
                "Esta intercorrência não é sobre furto/roubo/invasão/depredação."
            )
        return attrs
    
    def is_valid(self, raise_exception=False):

        valid = super().is_valid(raise_exception=False)
        if not valid:
            first_field, first_error_list = next(iter(self.errors.items()))
            message = first_error_list[0] if isinstance(first_error_list, list) else str(first_error_list)
            self._errors = {"detail": f"{first_field}: {message}"}

            if raise_exception:
                raise serializers.ValidationError(self._errors)

        return valid


class IntercorrenciaDiretorCompletoSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem do Diretor"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_extra = serializers.SerializerMethodField()
    smart_sampa_situacao_display = serializers.CharField(
        source='get_smart_sampa_situacao_display', read_only=True
    )
    tipos_ocorrencia = TipoOcorrenciaSerializer(many=True)

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