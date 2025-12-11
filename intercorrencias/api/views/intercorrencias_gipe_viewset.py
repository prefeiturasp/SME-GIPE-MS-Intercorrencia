from django.utils import timezone

from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status, mixins
from rest_framework.views import exception_handler
from rest_framework.permissions import IsAuthenticated

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.permissions import IntercorrenciaPermission
from intercorrencias.choices.gipe_choices import get_values_gipe_choices
from intercorrencias.api.serializers.intercorrencia_gipe_serializer import IntercorrenciaGipeSerializer, IntercorrenciaConclusaoGipeSerializer


class IntercorrenciaGipeViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet para GIPE - visualiza intercorrências e preenche campos próprios
    
    GET {uuid}/ - Detalhes
    PUT/PATCH {uuid}/ - Atualiza campos do GIPE
    PUT{uuid}/finalizar - Finaliza a intercorrência
    GET - gipe/categorias-disponiveis -> Lista todos os choices disponiveis para o GIPE
    """
    queryset = Intercorrencia.objects.all()
    serializer_class = IntercorrenciaGipeSerializer
    permission_classes = (IsAuthenticated, IntercorrenciaPermission)
    lookup_field = "uuid"

    def get_serializer_class(self):
        """
        Define dinamicamente o serializer com base na ação atual.
        """
        action_map = {
            "finalizar": IntercorrenciaConclusaoGipeSerializer,
        }
        return action_map.get(self.action, IntercorrenciaGipeSerializer)
    
    @action(detail=True, methods=['put'], url_path='finalizar')
    def finalizar(self, request, uuid=None):
        """PUT {uuid}/finalizar/ - Finaliza intercorrência"""
        
        try:
            instance = self.get_object()

            serializer = self.get_serializer(
                instance,
                data=request.data,
                partial=False,
                context={"request": request},
            )
            
            obj_to_update = {
                "status": "finalizada",
                "finalizado_gipe_em": timezone.now(),
                "finalizado_gipe_por": request.user.username,
                "atualizado_em": timezone.now()
            }          
            
            serializer.is_valid(raise_exception=True)
            serializer.save(**obj_to_update)
           
            serializer = IntercorrenciaConclusaoGipeSerializer(instance, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as exc:
            return self.handle_exception(exc)
    
    @action(detail=False, methods=['get'], url_path='categorias-disponiveis')
    def categorias_disponiveis(self, request):

        try:
            data = get_values_gipe_choices()
            return Response(data=data, status=status.HTTP_200_OK)
        
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