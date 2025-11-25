from rest_framework import serializers
from intercorrencias.api.serializers.intercorrencia_serializer import IntercorrenciaSerializer
from intercorrencias.models.intercorrencia import Intercorrencia

import logging
logger = logging.getLogger(__name__)


class IntercorrenciaDreSerializer(IntercorrenciaSerializer):
    """Serializer completo para DRE - preenche campos próprios"""
    
    # Campos booleanos obrigatórios
    acionamento_seguranca_publica = serializers.BooleanField(required=True)
    interlocucao_sts = serializers.BooleanField(required=True)
    interlocucao_cpca = serializers.BooleanField(required=True)
    interlocucao_supervisao_escolar = serializers.BooleanField(required=True)
    interlocucao_naapa = serializers.BooleanField(required=True)
    
    class Meta:
        model = Intercorrencia
        fields = (
            # Básicos (read-only para DRE)
            "id", "uuid", "unidade_codigo_eol", "dre_codigo_eol",
            
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
        
        