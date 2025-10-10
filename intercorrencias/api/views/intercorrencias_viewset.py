from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework import viewsets, mixins, status
from rest_framework.permissions import IsAuthenticated

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.api.serializers.intercorrencia_serializer import IntercorrenciaSerializer


class IntercorrenciaViewSet(mixins.CreateModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.ListModelMixin,
                            mixins.UpdateModelMixin,
                            viewsets.GenericViewSet):
    """
    /intercorrencias/ [GET, POST]
    /intercorrencias/{id}/ [GET]
    """
    queryset = Intercorrencia.objects.all()
    serializer_class = IntercorrenciaSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = "uuid"  # lookup por UUID, não por PK

    def perform_create(self, serializer):
        # `request.user` vem do nosso autenticador remoto. Ele possui `.username`.
        serializer.save(user_username=self.request.user.username)

    # filtros simples por query param
    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        eol = request.query_params.get("unidade")
        dre = request.query_params.get("dre")
        usuario = request.query_params.get("usuario")
        if eol:
            qs = qs.filter(unidade_codigo_eol=eol)
        if dre:
            qs = qs.filter(dre_codigo_eol=dre)
        if usuario:
            qs = qs.filter(user_username=usuario)
        page = self.paginate_queryset(qs)
        if page is not None:
            ser = self.get_serializer(page, many=True)
            return self.get_paginated_response(ser.data)
        ser = self.get_serializer(qs, many=True)
        return Response(ser.data, status=status.HTTP_200_OK)

    def handle_exception(self, exc):
        response = exception_handler(exc, self.get_exception_handler_context())

        if response is None:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(response.data, dict):
            detail = response.data.get("detail")
            if isinstance(detail, list) and len(detail) == 1:
                response.data["detail"] = detail[0]

        return response