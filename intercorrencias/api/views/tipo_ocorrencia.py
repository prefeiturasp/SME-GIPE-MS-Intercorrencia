from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia
from intercorrencias.api.serializers.tipo_ocorrencia_serializer import TipoOcorrenciaSerializer

class TipoOcorrenciaViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    API apenas para listar Tipos de Ocorrência (usado no select do front).
    """
    queryset = TipoOcorrencia.objects.filter(ativo=True).order_by("nome")
    serializer_class = TipoOcorrenciaSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "uuid"
