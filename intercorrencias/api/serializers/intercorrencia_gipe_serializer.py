import logging
from rest_framework import serializers

from intercorrencias.models.envolvido import Envolvido
from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia
from intercorrencias.api.serializers.intercorrencia_serializer import IntercorrenciaSerializer
from intercorrencias.api.serializers.tipo_ocorrencia_serializer import TipoOcorrenciaSerializer
from intercorrencias.choices.gipe_choices import (
    EnvolveArmaOuAtaque,
    AmeacaFoiRealizadaDeQualManeira,
    CicloAprendizagem
)
from intercorrencias.choices.info_agressor_choices import (
    MotivoOcorrencia
)

logger = logging.getLogger(__name__)


class IntercorrenciaGipeSerializer(IntercorrenciaSerializer):
    """Serializer completo para GIPE - preenche campos próprios"""

    envolve_arma_ataque = serializers.ChoiceField(
        choices=EnvolveArmaOuAtaque.choices,
        required=True,
        allow_blank=False
    )
    ameaca_realizada_qual_maneira = serializers.ChoiceField(
        choices=AmeacaFoiRealizadaDeQualManeira.choices,
        required=True,
        allow_blank=False
    )
    envolvido = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Envolvido.objects.all(),
        required=True
    )
    motivacao_ocorrencia = serializers.ListField(
        child=serializers.ChoiceField(choices=MotivoOcorrencia.choices),
        allow_empty=False,
    )
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
    qual_ciclo_aprendizagem = serializers.ChoiceField(
        choices=CicloAprendizagem.choices,
        required=True,
        allow_blank=False,
    )
    info_sobre_interacoes_virtuais_pessoa_agressora = serializers.CharField(required=False, allow_blank=True)
    encaminhamentos_gipe = serializers.CharField(required=True, allow_blank=False)
    
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    status_extra = serializers.SerializerMethodField()
    
    def get_status_extra(self, obj):
        return obj.STATUS_EXTRA_LABELS.get(obj.status)
    
    def validate_tipos_ocorrencia(self, value):
        if not value:
            raise serializers.ValidationError(
                "Este campo é obrigatório e não pode estar vazio."
            )
        return value
    
    class Meta:
        model = Intercorrencia
        fields = (
            "id", "uuid", "unidade_codigo_eol", "dre_codigo_eol", "status", "status_display", "status_extra",
            "envolve_arma_ataque", "ameaca_realizada_qual_maneira", "envolvido",
            "motivacao_ocorrencia", "tipos_ocorrencia", "tipos_ocorrencia_detalhes", "qual_ciclo_aprendizagem", 
            "info_sobre_interacoes_virtuais_pessoa_agressora", "encaminhamentos_gipe"
        )