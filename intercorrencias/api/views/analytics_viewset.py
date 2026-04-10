from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from config.settings import CODIGO_PERFIL_GIPE
from intercorrencias.services.analytics_service import AnalyticsService


class AnalyticsViewSet(viewsets.ViewSet):

    permission_classes = (IsAuthenticated,)

    def create(self, request):
        cargo_codigo = getattr(request.user, "cargo_codigo", None)

        if str(cargo_codigo) != str(CODIGO_PERFIL_GIPE):
            raise ValidationError({
                "detail": "Apenas usuários do GIPE podem acessar este recurso."
            })

        try:
            filtros = request.data or {}

            resultado = AnalyticsService().execute_pipeline_json(filtros)

            return Response(
                data=resultado,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )