import logging
from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import viewsets, permissions, status

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.api.serializers.verify_intercorrencia_serializer import VerifyIntercorrenciaSerializer
from config.settings import (
    CODIGO_PERFIL_DIRETOR,
    CODIGO_PERFIL_ASSISTENTE_DIRECAO,
    CODIGO_PERFIL_DRE,
    CODIGO_PERFIL_GIPE
)

logger = logging.getLogger(__name__)


class VerifyIntercorrenciaViewSet(viewsets.GenericViewSet):
    serializer_class = VerifyIntercorrenciaSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Intercorrencia.objects.all()
    lookup_field = "uuid"

    def retrieve(self, request, *args, **kwargs):
        user = request.user
        user_name = getattr(user, "username", None)
        perfil_codigo = getattr(user, "cargo_codigo", None)
        unidade_codigo_eol = getattr(user, "unidade_codigo_eol", None)

        logger.info(
            f"Usuário '{user_name}' (perfil: {perfil_codigo}) solicitou verificação de intercorrência UUID={kwargs.get('uuid')}."
        )

        try:
            intercorrencia = get_object_or_404(Intercorrencia, uuid=kwargs.get("uuid"))
        except Http404:
            logger.warning(
                f"Intercorrência UUID={kwargs.get('uuid')} não encontrada para o usuário '{user_name}'."
            )
            return Response(
                {"detail": "A intercorrência informada não existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        validators = {
            str(CODIGO_PERFIL_DRE): self._validate_dre,
            str(CODIGO_PERFIL_DIRETOR): self._validate_diretor_assistente,
            str(CODIGO_PERFIL_ASSISTENTE_DIRECAO): self._validate_diretor_assistente
        }

        if str(perfil_codigo) != str(CODIGO_PERFIL_GIPE):
            validator = validators.get(str(perfil_codigo))
            if not validator:
                logger.error(
                    f"Usuário '{user_name}' com perfil {perfil_codigo} tentou acessar intercorrência sem permissão."
                )
                return self._error("Perfil de usuário não autorizado para esta operação.")

            error = validator(intercorrencia, unidade_codigo_eol, user_name)
            if error:
                logger.warning(
                    f"Validação falhou para o usuário '{user_name}' na intercorrência UUID={intercorrencia.uuid}."
                )
                return error

        serializer = self.get_serializer(intercorrencia)
        logger.info(
            f"Usuário '{user_name}' acessou com sucesso a intercorrência UUID={intercorrencia.uuid}."
        )
        return Response(serializer.data)

    def _validate_dre(self, intercorrencia, unidade_codigo_eol, _user_name):
        if str(intercorrencia.dre_codigo_eol) != str(unidade_codigo_eol):
            logger.info(
                f"Validação DRE falhou: intercorrência {intercorrencia.uuid} pertence à DRE {intercorrencia.dre_codigo_eol}, "
                f"mas o usuário está na DRE {unidade_codigo_eol}."
            )
            return self._error("A unidade dessa intercorrência não pertence à sua DRE.")

    def _validate_diretor_assistente(self, intercorrencia, _unidade, user_name):
        if str(intercorrencia.user_username) != str(user_name):
            logger.info(
                f"Validação de autor falhou: intercorrência {intercorrencia.uuid} criada por "
                f"{intercorrencia.user_username}, acessada por {user_name}."
            )
            return self._error("Você só pode consultar intercorrências criadas por você.")

    def _error(self, detail):
        logger.error(f"Erro retornado: {detail}")
        return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)