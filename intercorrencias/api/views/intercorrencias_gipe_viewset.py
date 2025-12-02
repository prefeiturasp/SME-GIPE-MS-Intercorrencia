from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import viewsets, status
from rest_framework.views import exception_handler
from rest_framework.permissions import IsAuthenticated

from intercorrencias.permissions import IntercorrenciaPermission
from intercorrencias.choices.gipe_choices import get_values_gipe_choices


class IntercorrenciaGipeViewSet(viewsets.GenericViewSet):
    """
    ViewSet para GIPE - visualiza intercorrências e preenche campos próprios
    
    GET - gipe/categorias-disponiveis -> Lista todos os choices disponiveis para o GIPE
    """
    
    permission_classes = (IsAuthenticated, IntercorrenciaPermission)

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