import logging
from rest_framework import serializers

from intercorrencias.services import unidades_service
from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.api.serializers.intercorrencia_serializer import IntercorrenciaSerializer

logger = logging.getLogger(__name__)


class IntercorrenciaDreSerializer(IntercorrenciaSerializer):
    """Serializer completo para DRE - preenche campos próprios"""
    
    # Campos booleanos obrigatórios
    acionamento_seguranca_publica = serializers.BooleanField(required=True)
    interlocucao_sts = serializers.BooleanField(required=True)
    interlocucao_cpca = serializers.BooleanField(required=True)
    interlocucao_supervisao_escolar = serializers.BooleanField(required=True)
    interlocucao_naapa = serializers.BooleanField(required=True)
    
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    status_extra = serializers.SerializerMethodField()
    
    def get_status_extra(self, obj):
        return obj.STATUS_EXTRA_LABELS.get(obj.status)
    
    class Meta:
        model = Intercorrencia
        fields = (
            # Básicos (read-only para DRE)
            "id", "uuid", "unidade_codigo_eol", "dre_codigo_eol", "status", "status_display", "status_extra",
            
            # Campos próprios da DRE (editáveis)
            "acionamento_seguranca_publica", "interlocucao_sts", "info_complementar_sts",
            "interlocucao_cpca", "info_complementar_cpca", "interlocucao_supervisao_escolar", 
            "info_complementar_supervisao_escolar", "interlocucao_naapa", "info_complementar_naapa",

        )
        
    def validate(self, attrs):
        """
        Validações customizadas para campos da DRE:
        - Todos os campos booleanos são obrigatórios
        - Se interlocução é True, o campo info_complementar correspondente é obrigatório
        """
        attrs = super().validate(attrs)
        
        # Validação: se interlocucao_sts for True, info_complementar_sts é obrigatório
        if attrs.get("interlocucao_sts") is True:
            info_sts = attrs.get("info_complementar_sts", "").strip()
            if not info_sts:
                raise serializers.ValidationError({
                    "info_complementar_sts": "Este campo é obrigatório quando 'interlocucao_sts' é True."
                })
        
        # Validação: se interlocucao_cpca for True, info_complementar_cpca é obrigatório
        if attrs.get("interlocucao_cpca") is True:
            info_cpca = attrs.get("info_complementar_cpca", "").strip()
            if not info_cpca:
                raise serializers.ValidationError({
                    "info_complementar_cpca": "Este campo é obrigatório quando 'interlocucao_cpca' é True."
                })
        
        # Validação: se interlocucao_supervisao_escolar for True, info_complementar_supervisao_escolar é obrigatório
        if attrs.get("interlocucao_supervisao_escolar") is True:
            info_supervisao = attrs.get("info_complementar_supervisao_escolar", "").strip()
            if not info_supervisao:
                raise serializers.ValidationError({
                    "info_complementar_supervisao_escolar": "Este campo é obrigatório quando 'interlocucao_supervisao_escolar' é True."
                })
        
        # Validação: se interlocucao_naapa for True, info_complementar_naapa é obrigatório
        if attrs.get("interlocucao_naapa") is True:
            info_naapa = attrs.get("info_complementar_naapa", "").strip()
            if not info_naapa:
                raise serializers.ValidationError({
                    "info_complementar_naapa": "Este campo é obrigatório quando 'interlocucao_naapa' é True."
                })
        
        return attrs


class IntercorrenciaConclusaoDaDreSerializer(IntercorrenciaSerializer):
    """Serializer para conclusão da DRE"""
    
    motivo_encerramento_dre = serializers.CharField(required=True, allow_blank=False)
    nome_dre = serializers.SerializerMethodField()
    responsavel_nome = serializers.SerializerMethodField()
    responsavel_cpf = serializers.SerializerMethodField()
    responsavel_email = serializers.SerializerMethodField()

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
    
    class Meta:
        model = Intercorrencia
        fields = (
            "uuid",
            "unidade_codigo_eol",
            "dre_codigo_eol",
            "responsavel_cpf",
            "responsavel_nome",
            "responsavel_email",
            "nome_dre",
            "finalizado_dre_em",
            "finalizado_dre_por",
            "motivo_encerramento_dre",
            "protocolo_da_intercorrencia",
            "status_display",
            "status_extra",
        )
        read_only_fields = ("uuid",)