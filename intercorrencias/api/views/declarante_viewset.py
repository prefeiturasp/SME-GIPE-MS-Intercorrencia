from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from intercorrencias.models.declarante import Declarante
from intercorrencias.api.serializers.declarante_serializer import DeclaranteSerializer

class DeclaranteViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """
    API endpoint responsável por listar os declarantes ativos.
    """
    queryset = Declarante.objects.filter(ativo=True).order_by("declarante")
    serializer_class = DeclaranteSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "uuid"