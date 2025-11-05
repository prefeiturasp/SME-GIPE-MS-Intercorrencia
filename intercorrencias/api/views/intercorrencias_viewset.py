import logging

from django.utils import timezone
from config.settings import (
    CODIGO_PERFIL_DIRETOR,
    CODIGO_PERFIL_ASSISTENTE_DIRECAO,
    CODIGO_PERFIL_DRE
)

from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import exception_handler
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError 

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.permissions import IntercorrenciaPermission
from intercorrencias.api.serializers.intercorrencia_serializer import (
    IntercorrenciaSecaoInicialSerializer,
    IntercorrenciaDiretorCompletoSerializer,
    IntercorrenciaFurtoRouboSerializer,
    IntercorrenciaNaoFurtoRouboSerializer   
)

logger = logging.getLogger(__name__)

class IntercorrenciaDiretorViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    """
    ViewSet especializada para o fluxo de intercorrências.

    GET /api-intercorrencias/v1/diretor/
        → Retorna a listagem completa de intercorrências visíveis ao usuário autenticado.
    GET /api-intercorrencias/v1/diretor/{uuid}/
        → Retorna os detalhes de uma intercorrência específica.
    POST /api-intercorrencias/v1/diretor/secao-inicial/
        → Cria uma nova intercorrência (seção inicial).
    PUT /api-intercorrencias/v1/diretor/{uuid}/secao-inicial/
        → Atualiza os dados da seção inicial de uma intercorrência existente.
    PUT /api-intercorrencias/v1/diretor/{uuid}/furto-roubo/
        → Atualiza a seção de furto, roubo, invasão ou depredação.
    PUT /api-intercorrencias/v1/diretor/{uuid}/nao-furto-roubo/
    """

    queryset = Intercorrencia.objects.all()
    permission_classes = (IsAuthenticated, IntercorrenciaPermission)
    lookup_field = "uuid"

    def get_queryset(self):
        """
        Retorna as intercorrências com base na unidade do usuário autenticado.
        """
        qs = super().get_queryset()

        cargo_codigo = getattr(self.request.user, 'cargo_codigo', None)

        # Filtra apenas intercorrências da unidade do Diretor/ Assistente
        cargo_str = str(cargo_codigo)
        if cargo_str in [str(CODIGO_PERFIL_DIRETOR), str(CODIGO_PERFIL_ASSISTENTE_DIRECAO)]:
            user_name = getattr(self.request.user, 'username', None)
            if user_name:
                return qs.filter(user_username=user_name)
            
        # Filtra apenas intercorrências da DRE do ponto focal
        if cargo_str == str(CODIGO_PERFIL_DRE):
            user_unidade = getattr(self.request.user, 'unidade_codigo_eol', None)
            if user_unidade:
                return qs.filter(dre_codigo_eol=user_unidade)
            
        # Se não, retorna todos para o perfil GIPE
        return qs
    
    def get_serializer_class(self):
        """
        Define dinamicamente o serializer com base na ação atual.
        """
        action_map = {
            "secao_inicial_create": IntercorrenciaSecaoInicialSerializer,
            "secao_inicial_update": IntercorrenciaSecaoInicialSerializer,
            "furto_roubo": IntercorrenciaFurtoRouboSerializer,
            "nao_furto_roubo": IntercorrenciaNaoFurtoRouboSerializer
        }
        return action_map.get(self.action, IntercorrenciaDiretorCompletoSerializer)

    @action(detail=False, methods=["post"], url_path="secao-inicial")
    def secao_inicial_create(self, request):
        """ POST secao-inicial/ - Cria intercorrência com seção inicial """

        try:
            cargo_codigo = getattr(request.user, 'cargo_codigo', None)

            cargo_str = str(cargo_codigo)
            if cargo_str not in [str(CODIGO_PERFIL_DIRETOR), str(CODIGO_PERFIL_ASSISTENTE_DIRECAO)]:
                raise PermissionDenied("Apenas Diretor ou Assistente de Diretor podem criar intercorrências.")
        
            user_unidade = getattr(request.user, "unidade_codigo_eol", None)
            if not user_unidade:
                raise ValidationError({"detail": "Usuário sem unidade cadastrada."})

            serializer = self.get_serializer(data=request.data, partial=False, context={"request": request})
            serializer.is_valid(raise_exception=True)

            intercorrencia = serializer.save(
                user_username=request.user.username,
                unidade_codigo_eol=user_unidade,
                status="em_preenchimento_diretor",
                criado_em=timezone.now(),
            )

            response_serializer = IntercorrenciaSecaoInicialSerializer(intercorrencia)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except Exception as exc:
            return self.handle_exception(exc)

    @action(detail=True, methods=["put"], url_path="secao-inicial")
    def secao_inicial_update(self, request, uuid=None):

        try:
            instance = self.get_object()
            user_unidade = getattr(request.user, "unidade_codigo_eol", None)

            if not user_unidade:
                raise PermissionDenied({"detail": "Usuário sem unidade vinculada."})

            serializer = self.get_serializer(
                instance,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(atualizado_em=timezone.now())

            response_serializer = IntercorrenciaSecaoInicialSerializer(instance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as exc:
            return self.handle_exception(exc)

    @action(detail=True, methods=["put"], url_path="furto-roubo")
    def furto_roubo(self, request, uuid=None):

        try:
            instance = self.get_object()

            if hasattr(instance, "pode_ser_editado_por_diretor") and not instance.pode_ser_editado_por_diretor:
                return Response(
                    {"detail": "Esta intercorrência não pode mais ser editada."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = self.get_serializer(
                instance, data=request.data, partial=False, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(atualizado_em=timezone.now())

            response_serializer = IntercorrenciaFurtoRouboSerializer(instance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as exc:
            return self.handle_exception(exc)
    
    @action(detail=True, methods=["put"], url_path="nao-furto-roubo")
    def nao_furto_roubo(self, request, uuid=None):

        try:
            instance = self.get_object()

            if hasattr(instance, "pode_ser_editado_por_diretor") and not instance.pode_ser_editado_por_diretor:
                return Response(
                    {"detail": "Esta intercorrência não pode mais ser editada."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = self.get_serializer(
                instance, data=request.data, partial=False, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(atualizado_em=timezone.now())

            response_serializer = IntercorrenciaNaoFurtoRouboSerializer(instance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
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