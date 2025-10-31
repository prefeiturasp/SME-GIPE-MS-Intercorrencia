from rest_framework import serializers
from intercorrencias.models.declarante import Declarante

class DeclaranteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Declarante
        fields = ("uuid", "declarante")