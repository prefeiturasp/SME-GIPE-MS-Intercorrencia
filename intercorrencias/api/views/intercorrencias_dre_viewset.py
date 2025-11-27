import logging
from django.utils import timezone

from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import exception_handler
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.permissions import IntercorrenciaPermission

from intercorrencias.api.serializers.intercorrencia_dre_serializer import (
    IntercorrenciaDreSerializer,
    IntercorrenciaConclusaoDaDreSerializer,
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

    def get_serializer_class(self):
        """
        Define dinamicamente o serializer com base na ação atual.
        """
        action_map = {
            "enviar_para_gipe": IntercorrenciaConclusaoDaDreSerializer,
        }
        return action_map.get(self.action, IntercorrenciaDreSerializer)
    
    @action(detail=True, methods=['put'], url_path='enviar-para-gipe')
    def enviar_para_gipe(self, request, uuid=None):
        """PUT {uuid}/enviar-para-gipe/ - Finaliza e envia para GIPE"""
        
        try:
            instance = self.get_object()

            serializer = self.get_serializer(
                instance,
                data=request.data,
                partial=False,
                context={"request": request},
            )
            
            obj_to_update = {
                "status": "enviado_para_gipe",
                "finalizado_dre_em": timezone.now(),
                "finalizado_dre_por": request.user.username,
                "atualizado_em": timezone.now()
            }          
            
            serializer.is_valid(raise_exception=True)
            serializer.save(**obj_to_update)
           
            serializer = IntercorrenciaConclusaoDaDreSerializer(instance, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as exc:
            return self.handle_exception(exc)
        
    def handle_exception(self, exc):
        response = exception_handler(exc, self.get_exception_handler_context())

        if response is None:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(response.data, dict):
            detail = response.data.get("detail")
            if isinstance(detail, list) and len(detail) == 1:
                response.data["detail"] = detail[0]

        return response