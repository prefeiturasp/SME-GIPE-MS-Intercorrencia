from rest_framework import serializers
from intercorrencias.models.intercorrencia import Intercorrencia

class VerifyIntercorrenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Intercorrencia
        fields = "__all__"