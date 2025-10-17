import logging
from rest_framework.permissions import BasePermission, SAFE_METHODS
from config.settings import CODIGO_PERFIL_GIPE, CODIGO_PERFIL_DRE, CODIGO_PERFIL_DIRETOR

logger = logging.getLogger(__name__)

class IntercorrenciaPermission(BasePermission):
    """
    Permissões customizadas para intercorrências baseadas no perfil do usuário.
    """

    def has_permission(self, request, view):

        if request.user is None or not getattr(request.user, "is_authenticated", False):
            return False

        cargo_codigo = getattr(request.user, "cargo_codigo", None)
        if cargo_codigo is None:
            return False
        # normalize to string for comparison because settings may define codes as int or str
        cargo_str = str(cargo_codigo)
        if cargo_str not in [str(CODIGO_PERFIL_DIRETOR), str(CODIGO_PERFIL_DRE), str(CODIGO_PERFIL_GIPE)]:
            return False

        return True

    def has_object_permission(self, request, view, obj):

        if request.user is None or not getattr(request.user, "is_authenticated", False):
            return False

        cargo_codigo = getattr(request.user, "cargo_codigo", None)
        if cargo_codigo is None:
            return False

        cargo_str = str(cargo_codigo)
        if cargo_str == str(CODIGO_PERFIL_DIRETOR):
            return self._check_diretor_permission(request, obj)
        elif cargo_str == str(CODIGO_PERFIL_DRE):
            return self._check_dre_permission(request, obj)
        elif cargo_str == str(CODIGO_PERFIL_GIPE):
            return self._check_gipe_permission(request, obj)

        return False

    def _check_diretor_permission(self, request, obj):

        user_unidade = getattr(request.user, "unidade_codigo_eol", None)
        if not user_unidade:
            logger.warning(f"[PERMISSION] Usuário {request.user.username} sem unidade_codigo_eol")
            return False

        if getattr(obj, "unidade_codigo_eol", None) != user_unidade:
            return False

        if request.method in SAFE_METHODS or request.method == "POST":
            return True

        if request.method in ["PUT", "PATCH", "DELETE"]:
            return getattr(obj, "pode_ser_editado_por_diretor", False)

        return False

    def _check_dre_permission(self, request, obj):

        user_dre = getattr(request.user, "dre_codigo_eol", None)
        if not user_dre:
            logger.warning(f"[PERMISSION] Usuário {request.user.username} sem dre_codigo_eol")
            return False

        if getattr(obj, "dre_codigo_eol", None) != user_dre:
            return False

        if getattr(obj, "status", "") == "em_preenchimento_diretor":
            return False

        if request.method in SAFE_METHODS:
            return True

        if request.method in ["PUT", "PATCH"]:
            return getattr(obj, "pode_ser_editado_por_dre", False)

        return False

    def _check_gipe_permission(self, request, obj):

        if getattr(obj, "status", "") in ["em_preenchimento_diretor", "enviado_para_dre", "em_analise_dre"]:
            return False

        if request.method in SAFE_METHODS:
            return True

        if request.method in ["PUT", "PATCH"]:
            return getattr(obj, "pode_ser_editado_por_gipe", False)

        return False