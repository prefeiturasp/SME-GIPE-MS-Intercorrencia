from rest_framework import serializers

from intercorrencias.services import unidades_service
from intercorrencias.models.envolvido import Envolvido
from intercorrencias.models.declarante import Declarante
from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia
from intercorrencias.api.serializers.envolvido_serializer import EnvolvidoSerializer
from intercorrencias.api.serializers.declarante_serializer import DeclaranteSerializer
from intercorrencias.api.serializers.tipo_ocorrencia_serializer import TipoOcorrenciaSerializer
from intercorrencias.choices.info_agressor_choices import (
    MotivoOcorrencia,
    GrupoEtnicoRacial,
    Genero,
    FrequenciaEscolar,
    EtapaEscolar
)


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
    
    def is_valid(self, raise_exception=False):
        
        valid = super().is_valid(raise_exception=False)
        if not valid:
            first_field, first_error_list = next(iter(self.errors.items()))
            message = first_error_list[0] if isinstance(first_error_list, list) else str(first_error_list)

            if isinstance(self._errors, dict) and "detail" in self._errors:
                error_dict = self._errors
            else:
                error_dict = {"detail": f"{first_field}: {message}"}

            self._errors = error_dict

            if raise_exception:
                raise serializers.ValidationError(self._errors)

        return valid


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
            raise serializers.ValidationError({"detail": 
                "Esta intercorrência não é sobre furto/roubo/invasão/depredação."
            })
        return attrs
    
    
class IntercorrenciaSecaoFinalSerializer(IntercorrenciaSerializer):
    """Serializer para a seção final - Diretor"""

    declarante = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Declarante.objects.all(),
        required=True,
        write_only=True
    )
    declarante_detalhes = DeclaranteSerializer(
        read_only=True,
        source="declarante"
    )
    comunicacao_seguranca_publica = serializers.ChoiceField(
        choices=Intercorrencia.SEGURANCA_PUBLICA_CHOICES,
        required=True
    )
    protocolo_acionado = serializers.ChoiceField(
        choices=Intercorrencia.PROTOCOLO_CHOICES,
        required=True
    )

    class Meta:
        model = Intercorrencia
        fields = (
            "uuid",
            "unidade_codigo_eol",
            "dre_codigo_eol",
            "declarante",
            "declarante_detalhes",
            "comunicacao_seguranca_publica",
            "protocolo_acionado",
            "status_display",
            "status_extra",
        )
        read_only_fields = ("uuid", "status_display")

    
class IntercorrenciaNaoFurtoRouboSerializer(IntercorrenciaSerializer):
    """Serializer para intercorrências que NÃO são furto/roubo/invasão/depredação."""

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
    envolvido = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Envolvido.objects.all(),
        required=True,
        write_only=True
    )
    envolvido_detalhes = EnvolvidoSerializer(
        read_only=True,
        source="envolvido"
    )
    tem_info_agressor_ou_vitima = serializers.ChoiceField(
        choices=Intercorrencia.INFORMACOES_AGRESSOR_VITIMA_CHOICES,
        required=True
    )
    class Meta:
        model = Intercorrencia
        fields = (
            "uuid", "tipos_ocorrencia", "tipos_ocorrencia_detalhes", "descricao_ocorrencia", "envolvido", "envolvido_detalhes", "tem_info_agressor_ou_vitima",
            "status_display", "status_extra"
        )
        read_only_fields = ("uuid",)

    def validate_tipos_ocorrencia(self, value):
        if not value:
            raise serializers.ValidationError("Este campo é obrigatório e não pode estar vazio.")
        return value

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.sobre_furto_roubo_invasao_depredacao:
            raise serializers.ValidationError(
                "Esta intercorrência é de furto/roubo/invasão/depredação e deve usar o serializer correspondente."
            )
        return attrs
    

class IntercorrenciaInfoAgressorSerializer(IntercorrenciaSerializer):
    """Serializer para informações do agressor/vítima - Diretor"""

    nome_pessoa_agressora = serializers.CharField(required=True, allow_blank=False)
    idade_pessoa_agressora = serializers.IntegerField(required=True)
    motivacao_ocorrencia = serializers.ChoiceField(choices=MotivoOcorrencia.choices, required=True)
    genero_pessoa_agressora = serializers.ChoiceField(choices=Genero.choices, required=True)
    grupo_etnico_racial = serializers.ChoiceField(choices=GrupoEtnicoRacial.choices, required=True)
    etapa_escolar = serializers.ChoiceField(choices=EtapaEscolar.choices, required=True)
    frequencia_escolar = serializers.ChoiceField(choices=FrequenciaEscolar.choices, required=True)
    interacao_ambiente_escolar = serializers.CharField(required=True, allow_blank=False)
    redes_protecao_acompanhamento = serializers.CharField(required=True, allow_blank=False)
    notificado_conselho_tutelar = serializers.BooleanField(required=True)
    acompanhado_naapa = serializers.BooleanField(required=True)
    cep = serializers.CharField(required=True, allow_blank=False)
    logradouro = serializers.CharField(required=True, allow_blank=False)
    numero_residencia = serializers.CharField(required=True, allow_blank=False)
    complemento = serializers.CharField(required=False, allow_blank=True)
    bairro = serializers.CharField(required=True, allow_blank=False)
    cidade = serializers.CharField(required=True, allow_blank=False)
    estado = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = Intercorrencia
        fields = (
            "uuid", "unidade_codigo_eol", "dre_codigo_eol",
            "nome_pessoa_agressora", "idade_pessoa_agressora",
            "motivacao_ocorrencia", "genero_pessoa_agressora",
            "grupo_etnico_racial", "etapa_escolar", "frequencia_escolar",
            "interacao_ambiente_escolar", "redes_protecao_acompanhamento",
            "notificado_conselho_tutelar", "acompanhado_naapa",
            "cep", "logradouro", "numero_residencia", "complemento",
            "bairro", "cidade", "estado"
        )
        read_only_fields = ("uuid",)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = self.instance

        if instance and getattr(instance, "tem_info_agressor_ou_vitima", None) == "nao":
            raise serializers.ValidationError({
                'detail': "Não é possível preencher informações de agressor/vítima quando 'tem_info_agressor_ou_vitima' é False."
            })
        return attrs


class IntercorrenciaDiretorCompletoSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem do Diretor"""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_extra = serializers.SerializerMethodField()
    smart_sampa_situacao_display = serializers.CharField(
        source='get_smart_sampa_situacao_display', read_only=True
    )
    tipos_ocorrencia = TipoOcorrenciaSerializer(many=True)
    declarante_detalhes = DeclaranteSerializer(source="declarante", read_only=True)
    nome_unidade = serializers.SerializerMethodField()
    nome_dre = serializers.SerializerMethodField()
    envolvido = EnvolvidoSerializer(read_only=True)

    def get_status_extra(self, obj):
        return obj.STATUS_EXTRA_LABELS.get(obj.status)

    def get_nome_unidade(self, obj):
        """Obtém o nome da unidade via serviço externo."""
        try:
            unidade = unidades_service.get_unidade(obj.unidade_codigo_eol)
            return unidade.get("nome")
        except unidades_service.ExternalServiceError:
            return None

    def get_nome_dre(self, obj):
        """Obtém o nome da DRE via serviço externo."""
        try:
            dre = unidades_service.get_unidade(obj.dre_codigo_eol)
            return dre.get("nome")
        except unidades_service.ExternalServiceError:
            return None
    

    class Meta:
        model = Intercorrencia
        fields = (
            "id", "uuid", "status", "status_display", "status_extra",
            "criado_em", "atualizado_em",
            "data_ocorrencia", "unidade_codigo_eol", "dre_codigo_eol",
            "nome_unidade", "nome_dre", "user_username",
            "envolvido", "tem_info_agressor_ou_vitima",
            "sobre_furto_roubo_invasao_depredacao",
            "tipos_ocorrencia", "descricao_ocorrencia",
            "smart_sampa_situacao", "smart_sampa_situacao_display",
            "declarante_detalhes", "comunicacao_seguranca_publica", "protocolo_acionado",
        )
        read_only_fields = ("id", "uuid", "user_username", "criado_em", "atualizado_em")