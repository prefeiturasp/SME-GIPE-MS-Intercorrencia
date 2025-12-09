from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status, mixins
from rest_framework.views import exception_handler
from rest_framework.permissions import IsAuthenticated

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.permissions import IntercorrenciaPermission
from intercorrencias.choices.gipe_choices import get_values_gipe_choices
from intercorrencias.api.serializers.intercorrencia_gipe_serializer import IntercorrenciaGipeSerializer


class IntercorrenciaGipeViewSet(
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet
):
    """
    ViewSet para GIPE - visualiza intercorrências e preenche campos próprios
    
    GET {uuid}/ - Detalhes
    PUT/PATCH {uuid}/ - Atualiza campos do GIPE
    GET - gipe/categorias-disponiveis -> Lista todos os choices disponiveis para o GIPE
    """
    queryset = Intercorrencia.objects.all()
    serializer_class = IntercorrenciaGipeSerializer
    permission_classes = (IsAuthenticated, IntercorrenciaPermission)
    lookup_field = "uuid"
    
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