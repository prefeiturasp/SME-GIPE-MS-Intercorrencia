# intercorrencias/api/serializers/tipo_ocorrencia_serializer.py

from rest_framework import serializers
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia

class TipoOcorrenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoOcorrencia
        fields = ("uuid", "nome")
