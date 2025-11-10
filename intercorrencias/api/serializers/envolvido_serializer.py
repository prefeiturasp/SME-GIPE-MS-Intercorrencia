from rest_framework import serializers
from intercorrencias.models.envolvido import Envolvido

class EnvolvidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Envolvido
        fields = ["uuid", "perfil_dos_envolvidos"]
