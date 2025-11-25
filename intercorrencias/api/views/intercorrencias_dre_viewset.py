import logging
from rest_framework import viewsets, mixins

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.permissions import IntercorrenciaPermission

from intercorrencias.api.serializers.intercorrencia_dre_serializer import (
    IntercorrenciaDreSerializer,
)

from rest_framework.permissions import IsAuthenticated

from config.settings import (
    CODIGO_PERFIL_DRE
)


class IntercorrenciaDreViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet para DRE - visualiza intercorrências da sua DRE e preenche campos próprios
    
    GET / - Lista intercorrências da DRE
    GET {uuid}/ - Detalhes
    PUT/PATCH {uuid}/ - Atualiza campos da DRE
    POST {uuid}/enviar-para-gipe/ - Envia para GIPE
    """
    
    queryset = Intercorrencia.objects.all()
    serializer_class = IntercorrenciaDreSerializer
    permission_classes = (IsAuthenticated, IntercorrenciaPermission)
    lookup_field = "uuid"
    
    
    
