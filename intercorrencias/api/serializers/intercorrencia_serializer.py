from rest_framework import serializers

from config.settings import (
    CODIGO_PERFIL_DIRETOR,
    CODIGO_PERFIL_ASSISTENTE_DIRECAO,
    CODIGO_PERFIL_DRE,
    CODIGO_PERFIL_GIPE,
)
from intercorrencias.services import unidades_service
from intercorrencias.models.envolvido import Envolvido
from intercorrencias.models.declarante import Declarante
from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia
from intercorrencias.api.serializers.envolvido_serializer import EnvolvidoSerializer
from intercorrencias.api.serializers.declarante_serializer import DeclaranteSerializer
from intercorrencias.api.serializers.tipo_ocorrencia_serializer import (
    TipoOcorrenciaSerializer,
)
from intercorrencias.choices.info_agressor_choices import (
    MotivoOcorrencia,
    GrupoEtnicoRacial,
    Genero,
    FrequenciaEscolar,
    EtapaEscolar,
)

import logging
logger = logging.getLogger(__name__)


class IntercorrenciaSerializer(serializers.ModelSerializer):

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    status_extra = serializers.SerializerMethodField()

    def get_status_extra(self, obj):
        return obj.STATUS_EXTRA_LABELS.get(obj.status)
    
    def _get_campos_agressor_vitima(self):
        """Retorna a lista de campos relacionados a informações de agressor/vítima"""
        return [
            "nome_pessoa_agressora",
            "idade_pessoa_agressora",
            "genero_pessoa_agressora",
            "grupo_etnico_racial",
            "etapa_escolar",
            "frequencia_escolar",
            "interacao_ambiente_escolar",
            "redes_protecao_acompanhamento",
            "notificado_conselho_tutelar",
            "acompanhado_naapa",
            "cep",
            "logradouro",
            "numero_residencia",
            "complemento",
            "bairro",
            "cidade",
            "estado",
        ]

    def _limpar_campos_agressor_vitima(self, instance, campos):
        """Limpa os campos de agressor/vítima na instância"""
        for campo in campos:
            if campo in ["idade_pessoa_agressora", "notificado_conselho_tutelar", "acompanhado_naapa"]:
                setattr(instance, campo, None)
        instance.save(update_fields=campos)

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
            raise serializers.ValidationError(
                {"detail": "DRE informada não corresponde à DRE da unidade."}
            )

        user_unidade = getattr(request.user, "unidade_codigo_eol", None)
        is_gipe_user = getattr(request.user, "cargo_codigo", None) == int(CODIGO_PERFIL_GIPE)
        if not is_gipe_user and (not user_unidade or user_unidade not in (codigo_unidade, codigo_dre)):
            raise serializers.ValidationError(
                {"detail": "A unidade não pertence ao usuário autenticado."}
            )

        return attrs

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


class IntercorrenciaSecaoInicialSerializer(IntercorrenciaSerializer):
    """Serializer para a seção inicial - Diretor"""

    class Meta:
        model = Intercorrencia
        fields = (
            "uuid",
            "data_ocorrencia",
            "unidade_codigo_eol",
            "dre_codigo_eol",
            "sobre_furto_roubo_invasao_depredacao",
            "status_display",
            "status_extra",
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
        write_only=True,
    )
    tipos_ocorrencia_detalhes = TipoOcorrenciaSerializer(
        many=True, read_only=True, source="tipos_ocorrencia"
    )
    descricao_ocorrencia = serializers.CharField(required=True, allow_blank=False)
    smart_sampa_situacao = serializers.ChoiceField(
        required=True, allow_blank=False, choices=Intercorrencia.SMART_SAMPA_CHOICES
    )

    class Meta:
        model = Intercorrencia
        fields = (
            "uuid",
            "tipos_ocorrencia",
            "tipos_ocorrencia_detalhes",
            "descricao_ocorrencia",
            "smart_sampa_situacao",
            "status_display",
            "status_extra",
        )
        read_only_fields = ("uuid",)

    def validate_tipos_ocorrencia(self, value):
        if not value:
            raise serializers.ValidationError(
                "Este campo é obrigatório e não pode estar vazio."
            )
        return value

    def validate(self, attrs):
        instance = self.instance
        if instance and not instance.sobre_furto_roubo_invasao_depredacao:
            raise serializers.ValidationError(
                {
                    "detail": "Esta intercorrência não é sobre furto/roubo/invasão/depredação."
                }
            )
        return attrs
    
    def update(self, instance, validated_data):
        """
        Garante que campos não aplicáveis sejam limpos quando é furto/roubo.
        Segue padrão de 2 etapas:
        - ETAPA 1: Remove campos não aplicáveis do validated_data ANTES do update
        - ETAPA 2: Limpa campos na instância APÓS o update
        """
        
        # ETAPA 1: Remove campos não aplicáveis do validated_data ANTES do update
        # Furto/roubo não possui envolvido nem informações de agressor/vítima
        validated_data.pop("tem_info_agressor_ou_vitima", None)
        
        campos_agressor_vitima = self._get_campos_agressor_vitima()
        
        # Remove também todos os campos de agressor/vítima
        for campo in campos_agressor_vitima:
            validated_data.pop(campo, None)
        
        # Atualiza a instância com os dados validados
        instance = super().update(instance, validated_data)
        
        # ETAPA 2: Limpa campos na instância APÓS o update
        instance.tem_info_agressor_ou_vitima = ""
        instance.save(update_fields=["tem_info_agressor_ou_vitima"])
        
        # Limpa todos os campos de agressor/vítima
        self._limpar_campos_agressor_vitima(instance, campos_agressor_vitima)

        return instance 


class IntercorrenciaSecaoFinalSerializer(IntercorrenciaSerializer):
    """Serializer para a seção final - Diretor"""

    declarante = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Declarante.objects.all(),
        required=True,
        write_only=True,
    )
    declarante_detalhes = DeclaranteSerializer(read_only=True, source="declarante")
    comunicacao_seguranca_publica = serializers.ChoiceField(
        choices=Intercorrencia.SEGURANCA_PUBLICA_CHOICES, required=True
    )
    protocolo_acionado = serializers.ChoiceField(
        choices=Intercorrencia.PROTOCOLO_CHOICES, required=True
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
        write_only=True,
    )
    tipos_ocorrencia_detalhes = TipoOcorrenciaSerializer(
        many=True, read_only=True, source="tipos_ocorrencia"
    )
    descricao_ocorrencia = serializers.CharField(required=True, allow_blank=False)
    envolvido = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Envolvido.objects.all(),
        required=True,
        write_only=True,
    )
    envolvido_detalhes = EnvolvidoSerializer(read_only=True, source="envolvido")
    tem_info_agressor_ou_vitima = serializers.ChoiceField(
        choices=Intercorrencia.INFORMACOES_AGRESSOR_VITIMA_CHOICES, required=True
    )

    class Meta:
        model = Intercorrencia
        fields = (
            "uuid",
            "tipos_ocorrencia",
            "tipos_ocorrencia_detalhes",
            "descricao_ocorrencia",
            "envolvido",
            "envolvido_detalhes",
            "tem_info_agressor_ou_vitima",
            "status_display",
            "status_extra",
        )
        read_only_fields = ("uuid",)

    def validate_tipos_ocorrencia(self, value):
        if not value:
            raise serializers.ValidationError(
                "Este campo é obrigatório e não pode estar vazio."
            )
        return value

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.sobre_furto_roubo_invasao_depredacao:
            raise serializers.ValidationError(
                "Esta intercorrência é de furto/roubo/invasão/depredação e deve usar o serializer correspondente."
            )
        return attrs
    
    def update(self, instance, validated_data):
        """
        Garante que campos não aplicáveis sejam limpos quando NÃO é furto/roubo.
        Segue padrão de 2 etapas:
        - ETAPA 1: Remove campos não aplicáveis do validated_data ANTES do update
        - ETAPA 2: Limpa campos na instância APÓS o update
        """
        
        # # ETAPA 1: Remove campos não aplicáveis do validated_data ANTES do update
        # # Não-furto/roubo não possui smart_sampa_situacao
        validated_data.pop("smart_sampa_situacao", None)
        
        tem_info_agressor_ou_vitima = validated_data.get(
            "tem_info_agressor_ou_vitima", instance.tem_info_agressor_ou_vitima
        )
        
        campos_agressor_vitima = self._get_campos_agressor_vitima()
        
        if tem_info_agressor_ou_vitima != "sim":
            for campo in campos_agressor_vitima:
                validated_data.pop(campo, None)
            
        # Atualiza a instância com os dados validados
        instance = super().update(instance, validated_data)
        
        # ETAPA 2: Limpa campos na instância APÓS o update
        instance.smart_sampa_situacao = ""
        instance.save(update_fields=["smart_sampa_situacao"])
        
        if tem_info_agressor_ou_vitima != "sim":
            self._limpar_campos_agressor_vitima(instance, campos_agressor_vitima)

        return instance    


class IntercorrenciaInfoAgressorSerializer(IntercorrenciaSerializer):
    """Serializer para informações do agressor/vítima - Diretor"""

    nome_pessoa_agressora = serializers.CharField(required=True, allow_blank=False)
    idade_pessoa_agressora = serializers.IntegerField(required=True)
    motivacao_ocorrencia = serializers.ListField(
        child=serializers.ChoiceField(choices=MotivoOcorrencia.choices),
        allow_empty=False,  # se quiser obrigar pelo menos 1 motivo
    )
    motivacao_ocorrencia_display = serializers.SerializerMethodField(read_only=True)
    genero_pessoa_agressora = serializers.ChoiceField(
        choices=Genero.choices, required=True
    )
    grupo_etnico_racial = serializers.ChoiceField(
        choices=GrupoEtnicoRacial.choices, required=True
    )
    etapa_escolar = serializers.ChoiceField(choices=EtapaEscolar.choices, required=True)
    frequencia_escolar = serializers.ChoiceField(
        choices=FrequenciaEscolar.choices, required=True
    )
    interacao_ambiente_escolar = serializers.CharField(required=True, allow_blank=False)
    redes_protecao_acompanhamento = serializers.CharField(
        required=True, allow_blank=False
    )
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
            "uuid",
            "unidade_codigo_eol",
            "dre_codigo_eol",
            "nome_pessoa_agressora",
            "idade_pessoa_agressora",
            "motivacao_ocorrencia",
            "motivacao_ocorrencia_display",
            "genero_pessoa_agressora",
            "grupo_etnico_racial",
            "etapa_escolar",
            "frequencia_escolar",
            "interacao_ambiente_escolar",
            "redes_protecao_acompanhamento",
            "notificado_conselho_tutelar",
            "acompanhado_naapa",
            "cep",
            "logradouro",
            "numero_residencia",
            "complemento",
            "bairro",
            "cidade",
            "estado",
        )
        read_only_fields = ("uuid",)

    def get_motivacao_ocorrencia_display(self, obj):
        """Retorna os labels das motivações selecionadas"""
        if not obj.motivacao_ocorrencia:
            return []

        choices_dict = dict(MotivoOcorrencia.choices)
        return [
            {"value": motivo, "label": choices_dict.get(motivo, motivo)}
            for motivo in obj.motivacao_ocorrencia
        ]

    def validate_motivacao_ocorrencia(self, value):
        """Valida as motivações selecionadas"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("Selecione pelo menos uma motivação.")

        # Validar que todos os valores são válidos
        valid_choices = [choice[0] for choice in MotivoOcorrencia.choices]

        for motivo in value:
            if motivo not in valid_choices:
                raise serializers.ValidationError(
                    f"'{motivo}' não é uma motivação válida."
                )

        # Remover duplicatas
        return list(set(value))

    def validate(self, attrs):
        attrs = super().validate(attrs)
        instance = self.instance

        if instance and getattr(instance, "tem_info_agressor_ou_vitima", None) == "nao":
            raise serializers.ValidationError(
                {
                    "detail": "Não é possível preencher informações de agressor/vítima quando 'tem_info_agressor_ou_vitima' é False."
                }
            )
        return attrs
    
class IntercorrenciaConclusaoDaUeSerializer(IntercorrenciaSerializer):
    """Serializer para conclusão da UE - Diretor"""
    
    motivo_encerramento_ue = serializers.CharField(required=True, allow_blank=False)
    nome_unidade = serializers.SerializerMethodField()
    nome_dre = serializers.SerializerMethodField()
    responsavel_nome = serializers.SerializerMethodField()
    responsavel_cpf = serializers.SerializerMethodField()
    responsavel_email = serializers.SerializerMethodField()
    perfil_acesso = serializers.SerializerMethodField()
    
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
    
    def get_responsavel_nome(self, obj):
        """Obtém o nome do usuário responsável do contexto da requisição"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return getattr(request.user, 'name', None)
        return None
    
    def get_responsavel_cpf(self, obj):
        """Obtém o CPF do usuário responsável do contexto da requisição"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            
            cpf = getattr(request.user, 'cpf', None)
            if cpf and cpf.isdigit() and len(cpf) == 11:
                # Formata CPF: 123.456.789-01
                return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
            return cpf
        return None
    
    def get_responsavel_email(self, obj):
        """Obtém o email do usuário responsável do contexto da requisição"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            return getattr(request.user, 'email', None)
        return None
    
    def get_perfil_acesso(self, obj):
        """Obtém o perfil de acesso do usuário"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            cargo_codigo = getattr(request.user, 'cargo_codigo', None)
            # Mapeia códigos de cargo para nomes legíveis
            perfis = {
                str(CODIGO_PERFIL_DIRETOR): "Diretor(a) Pedagógico",
                str(CODIGO_PERFIL_ASSISTENTE_DIRECAO): "Assistente de Direção",
                str(CODIGO_PERFIL_DRE): "Ponto Focal DRE",
                str(CODIGO_PERFIL_GIPE): "Ponto Focal DRE",
            }
            return perfis.get(str(cargo_codigo), "Não definido")
        return None

    
    class Meta:
        model = Intercorrencia
        fields = (
            "uuid",
            "responsavel_nome",
            "responsavel_cpf",
            "responsavel_email",
            "perfil_acesso",
            "unidade_codigo_eol",
            "dre_codigo_eol",
            "nome_unidade",
            "nome_dre",
            "finalizado_diretor_em",
            "finalizado_diretor_por",
            "motivo_encerramento_ue",
            "protocolo_da_intercorrencia",
            "status_display",
            "status_extra",
        )
        read_only_fields = ("uuid",)
        
    def validate(self, attrs):
        return super().validate(attrs)    


class IntercorrenciaDiretorCompletoListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        if isinstance(data, list) or hasattr(data, '__iter__'):
            codigos = {obj.unidade_codigo_eol for obj in data} | {obj.dre_codigo_eol for obj in data}
            codigos = {str(c) for c in codigos if c}
            self.child.context["cache_unidades"] = unidades_service.get_unidades_em_lote(codigos)

        return super().to_representation(data)
    

class IntercorrenciaDiretorCompletoSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem do Diretor"""

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    status_extra = serializers.SerializerMethodField()
    smart_sampa_situacao_display = serializers.CharField(
        source="get_smart_sampa_situacao_display", read_only=True
    )
    tipos_ocorrencia = TipoOcorrenciaSerializer(many=True)
    declarante_detalhes = DeclaranteSerializer(source="declarante", read_only=True)
    nome_unidade = serializers.SerializerMethodField()
    nome_dre = serializers.SerializerMethodField()
    envolvido = EnvolvidoSerializer(read_only=True)
    motivacao_ocorrencia_display = serializers.SerializerMethodField(read_only=True)

    def get_motivacao_ocorrencia_display(self, obj):
        """Retorna os labels das motivações selecionadas"""
        if not obj.motivacao_ocorrencia:
            return []

        choices_dict = dict(MotivoOcorrencia.choices)
        return [
            {"value": motivo, "label": choices_dict.get(motivo, motivo)}
            for motivo in obj.motivacao_ocorrencia
        ]

    def get_status_extra(self, obj):
        return obj.STATUS_EXTRA_LABELS.get(obj.status)

    def get_nome_unidade(self, obj):
        cache = self.context.get("cache_unidades", {})
        return cache.get(str(obj.unidade_codigo_eol), {}).get("nome")

    def get_nome_dre(self, obj):
        cache = self.context.get("cache_unidades", {})
        return cache.get(str(obj.dre_codigo_eol), {}).get("nome")
    
    def to_representation(self, instance):
        if "cache_unidades" not in self.context:
            codigos = set()

            if instance.unidade_codigo_eol:
                codigos.add(str(instance.unidade_codigo_eol))
            if instance.dre_codigo_eol:
                codigos.add(str(instance.dre_codigo_eol))

            self.context["cache_unidades"] = unidades_service.get_unidades_em_lote(codigos)

        return super().to_representation(instance)

    class Meta:
        model = Intercorrencia
        fields = (
            "id",
            "uuid",
            "status",
            "status_display",
            "status_extra",
            "criado_em",
            "atualizado_em",
            "data_ocorrencia",
            "unidade_codigo_eol",
            "dre_codigo_eol",
            "nome_unidade",
            "nome_dre",
            "user_username",
            "envolvido",
            "tem_info_agressor_ou_vitima",
            "sobre_furto_roubo_invasao_depredacao",
            "tipos_ocorrencia",
            "descricao_ocorrencia",
            "smart_sampa_situacao",
            "smart_sampa_situacao_display",
            "declarante_detalhes",
            "comunicacao_seguranca_publica",
            "protocolo_acionado",
            "nome_pessoa_agressora",
            "idade_pessoa_agressora",
            "motivacao_ocorrencia_display",
            "genero_pessoa_agressora",
            "grupo_etnico_racial",
            "etapa_escolar",
            "frequencia_escolar",
            "interacao_ambiente_escolar",
            "redes_protecao_acompanhamento",
            "notificado_conselho_tutelar",
            "acompanhado_naapa",
            "cep",
            "logradouro",
            "numero_residencia",
            "complemento",
            "bairro",
            "cidade",
            "estado",
            "protocolo_da_intercorrencia",
            "motivo_encerramento_ue",
            "finalizado_diretor_em",
            "finalizado_diretor_por",
        )
        read_only_fields = ("id", "uuid", "user_username", "criado_em", "atualizado_em")
        list_serializer_class = IntercorrenciaDiretorCompletoListSerializer


class IntercorrenciaUpdateDiretorCompletoSerializer(IntercorrenciaSerializer):
    """
    Serializer para atualização completa de uma intercorrência.
    Aceita todos os campos e aplica regras de limpeza baseadas no tipo.
    """

    tipos_ocorrencia = serializers.SlugRelatedField(
        many=True,
        slug_field="uuid",
        queryset=TipoOcorrencia.objects.all(),
        required=False,
        write_only=True,
    )

    descricao_ocorrencia = serializers.CharField(required=False, allow_blank=True)
    smart_sampa_situacao = serializers.ChoiceField(
        required=False, allow_blank=True, choices=Intercorrencia.SMART_SAMPA_CHOICES
    )
    envolvido = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Envolvido.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    tem_info_agressor_ou_vitima = serializers.ChoiceField(
        choices=Intercorrencia.INFORMACOES_AGRESSOR_VITIMA_CHOICES,
        required=False,
        allow_blank=True,
    )
    declarante = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Declarante.objects.all(),
        required=False,
        allow_null=True,
        write_only=True,
    )

    comunicacao_seguranca_publica = serializers.ChoiceField(
        choices=Intercorrencia.SEGURANCA_PUBLICA_CHOICES,
        required=False,
        allow_blank=True,
    )
    protocolo_acionado = serializers.ChoiceField(
        choices=Intercorrencia.PROTOCOLO_CHOICES, required=False, allow_blank=True
    )

    class Meta:
        model = Intercorrencia
        fields = (
            "uuid",
            "data_ocorrencia",
            "unidade_codigo_eol",
            "dre_codigo_eol",
            "sobre_furto_roubo_invasao_depredacao",
            "tipos_ocorrencia",
            "descricao_ocorrencia",
            "smart_sampa_situacao",
            "envolvido",
            "tem_info_agressor_ou_vitima",
            "declarante",
            "comunicacao_seguranca_publica",
            "protocolo_acionado",
            "nome_pessoa_agressora",
            "idade_pessoa_agressora",
            "motivacao_ocorrencia",
            "genero_pessoa_agressora",
            "grupo_etnico_racial",
            "etapa_escolar",
            "frequencia_escolar",
            "interacao_ambiente_escolar",
            "redes_protecao_acompanhamento",
            "notificado_conselho_tutelar",
            "acompanhado_naapa",
            "cep",
            "logradouro",
            "numero_residencia",
            "complemento",
            "bairro",
            "cidade",
            "estado",
        )
        read_only_fields = ("uuid", "status_display")

    def update(self, instance, validated_data):
        """
        Aplica regras de limpeza baseadas no tipo de intercorrência:
        - Se É furto/roubo: limpa envolvido e tem_info_agressor_ou_vitima
        - Se NÃO É furto/roubo: limpa smart_sampa_situacao
        - Se tem_info != "sim": limpa campos de agressor/vítima
        """
        # Verifica se é sobre furto/roubo (pode estar em validated_data ou já na instância)
        sobre_furto_roubo = validated_data.get(
            "sobre_furto_roubo_invasao_depredacao",
            instance.sobre_furto_roubo_invasao_depredacao,
        )

        campos_agressor_vitima = self._get_campos_agressor_vitima()

        # ETAPA 1: Remove campos não aplicáveis do validated_data ANTES do update
        if sobre_furto_roubo:
            validated_data.pop("tem_info_agressor_ou_vitima", None)
            
            # Remove também campos agressor/vítima pois não se aplicam a furto/roubo
            for campo in campos_agressor_vitima:
                validated_data.pop(campo, None)
        else:
            validated_data.pop("smart_sampa_situacao", None)
            
        tem_info_agressor_ou_vitima = validated_data.get(
            "tem_info_agressor_ou_vitima", instance.tem_info_agressor_ou_vitima
        )

        # Só verifica tem_info se NÃO for furto/roubo (já foi tratado acima)
        if not sobre_furto_roubo and tem_info_agressor_ou_vitima != "sim":
            for campo in campos_agressor_vitima:
                validated_data.pop(campo, None)

        # Atualiza a instância com os dados validados
        instance = super().update(instance, validated_data)

        # ETAPA 2: Após atualizar, garante que os campos foram limpos na instância
        if sobre_furto_roubo:
            instance.tem_info_agressor_ou_vitima = ""
            instance.save(update_fields=["tem_info_agressor_ou_vitima"])
        else:
            instance.smart_sampa_situacao = ""
            instance.save(update_fields=["smart_sampa_situacao"])

        if tem_info_agressor_ou_vitima != "sim" or sobre_furto_roubo:
            self._limpar_campos_agressor_vitima(instance, campos_agressor_vitima)

        return instance