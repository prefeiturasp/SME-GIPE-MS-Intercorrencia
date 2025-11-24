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
from intercorrencias.choices.info_agressor_choices import get_values_info_agressor_choices
from intercorrencias.api.serializers.intercorrencia_serializer import (
    IntercorrenciaSecaoInicialSerializer,
    IntercorrenciaDiretorCompletoSerializer,
    IntercorrenciaUpdateDiretorCompletoSerializer,
    IntercorrenciaFurtoRouboSerializer,
    IntercorrenciaNaoFurtoRouboSerializer,
    IntercorrenciaSecaoFinalSerializer,
    IntercorrenciaInfoAgressorSerializer,
    IntercorrenciaConclusaoDaUeSerializer
)

logger = logging.getLogger(__name__)
MSG_INTERCORRENCIA_NAO_EDITAVEL = "Esta intercorrência não pode mais ser editada."


class IntercorrenciaDiretorViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    """
    ViewSet especializada para o fluxo de intercorrências.

    GET /api-intercorrencias/v1/diretor/
        → Retorna a listagem completa de intercorrências visíveis ao usuário autenticado.
    GET /api-intercorrencias/v1/diretor/{uuid}/
        → Retorna os detalhes de uma intercorrência específica.
    GET /api-intercorrencias/v1/diretor/categorias-disponiveis
    POST /api-intercorrencias/v1/diretor/secao-inicial/
        → Cria uma nova intercorrência (seção inicial).
    PUT /api-intercorrencias/v1/diretor/{uuid}/secao-inicial/
        → Atualiza os dados da seção inicial de uma intercorrência existente.
    PUT /api-intercorrencias/v1/diretor/{uuid}/furto-roubo/
    PUT /api-intercorrencias/v1/diretor/{uuid}/nao-furto-roubo/
    PUT /api-intercorrencias/v1/diretor/{uuid}/secao-final/
    PUT /api-intercorrencias/v1/diretor/{uuid}/info-agressor/
    PUT /api-intercorrencias/v1/diretor/{uuid}/enviar-para-dre/
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
            "nao_furto_roubo": IntercorrenciaNaoFurtoRouboSerializer,
            "secao_final": IntercorrenciaSecaoFinalSerializer,
            "info_agressor": IntercorrenciaInfoAgressorSerializer,
            "enviar_para_dre": IntercorrenciaConclusaoDaUeSerializer,
            "update": IntercorrenciaUpdateDiretorCompletoSerializer,
            "partial_update": IntercorrenciaUpdateDiretorCompletoSerializer,
        }
        return action_map.get(self.action, IntercorrenciaDiretorCompletoSerializer)
    
    def update(self, request, uuid=None):
        """PUT {uuid}/ - Atualiza intercorrência completa"""

        try:
            instance = self.get_object()
            
            if not instance.pode_ser_editado_por_diretor:
                return Response(
                    {"detail": MSG_INTERCORRENCIA_NAO_EDITAVEL},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            serializer = self.get_serializer(
                instance, 
                data=request.data, 
                partial=True,
                context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(atualizado_em=timezone.now())
            
            # Retorna com o serializer completo para mostrar todos os dados
            response_serializer = IntercorrenciaDiretorCompletoSerializer(instance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as exc:
            return self.handle_exception(exc)

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

            serializer = self.get_serializer(
                instance, data=request.data, partial=False, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(atualizado_em=timezone.now())

            response_serializer = IntercorrenciaNaoFurtoRouboSerializer(instance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        except Exception as exc:
            return self.handle_exception(exc)
    
    @action(detail=True, methods=["put"], url_path="secao-final")
    def secao_final(self, request, uuid=None):

        try:
            instance = self.get_object()

            serializer = self.get_serializer(
                instance,
                data=request.data,
                partial=False,
                context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(atualizado_em=timezone.now())

            response_serializer = IntercorrenciaSecaoFinalSerializer(instance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as exc:
            return self.handle_exception(exc)

    @action(detail=True, methods=["put"], url_path="info-agressor")
    def info_agressor(self, request, uuid=None):
        """PUT {uuid}/info-agressor/ - Preenche informações do agressor/vítima"""

        try:
            instance = self.get_object()
            if getattr(instance, "tem_info_agressor_ou_vitima", None) == "nao":
                return Response(
                    {"detail": "Só é possível preencher informações quando 'tem_info_agressor_ou_vitima' é verdadeiro."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = self.get_serializer(instance, data=request.data, partial=False)
            serializer.is_valid(raise_exception=True)
            serializer.save(atualizado_em=timezone.now())

            response_serializer = IntercorrenciaInfoAgressorSerializer(instance)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as exc:
            return self.handle_exception(exc)
       
    @action(detail=True, methods=['put'], url_path='enviar-para-dre')
    def enviar_para_dre(self, request, uuid=None):
        """PUT {uuid}/enviar-para-dre/ - Finaliza e envia para DRE"""
        
        try:
            instance = self.get_object()

            serializer = self.get_serializer(
                instance,
                data=request.data,
                partial=False,
                context={"request": request},
            )
            
            obj_to_update = {
                "status": "enviado_para_dre",
                "finalizado_diretor_em": timezone.now(),
                "finalizado_diretor_por": request.user.username,
                "atualizado_em": timezone.now()
            }   
            
            if not instance.protocolo_da_intercorrencia:
                obj_to_update["protocolo_da_intercorrencia"] = Intercorrencia.gerar_protocolo()         
            
            serializer.is_valid(raise_exception=True)
            serializer.save(**obj_to_update)
           
            serializer = IntercorrenciaConclusaoDaUeSerializer(instance, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as exc:
            return self.handle_exception(exc)
        
    @action(detail=False, methods=['get'], url_path='categorias-disponiveis')
    def categorias_disponiveis(self, request):

        try:
            data = get_values_info_agressor_choices()
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