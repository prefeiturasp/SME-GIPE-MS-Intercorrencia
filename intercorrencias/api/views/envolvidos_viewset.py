from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from intercorrencias.models.envolvido import Envolvido
from intercorrencias.api.serializers.envolvido_serializer import EnvolvidoSerializer

class EnvolvidoViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API para listar os tipos de envolvidos.
    """
    queryset = Envolvido.objects.filter(ativo=True).order_by("perfil_dos_envolvidos")
    serializer_class = EnvolvidoSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "uuid"
