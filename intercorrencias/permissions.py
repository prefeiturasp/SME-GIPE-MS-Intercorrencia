import logging
from rest_framework.permissions import BasePermission, SAFE_METHODS
from config.settings import (
    CODIGO_PERFIL_GIPE,
    CODIGO_PERFIL_DRE,
    CODIGO_PERFIL_DIRETOR,
    CODIGO_PERFIL_ASSISTENTE_DIRECAO,
)
 
logger = logging.getLogger(__name__)
 
class IntercorrenciaPermission(BasePermission):
    """
    Permissões customizadas para intercorrências baseadas no perfil do usuário.
    """
 
    def has_permission(self, request, view):
 
        if request.user is None or not getattr(request.user, "is_authenticated", False):
            logger.info("[PERMISSION] Usuário anônimo tentando acessar %s", view.__class__.__name__)
            return False
 
        cargo_codigo = getattr(request.user, "cargo_codigo", None)
        if cargo_codigo is None:
            logger.info("[PERMISSION] Usuário %s sem cargo definido", request.user.username)
            return False
        
        cargo_str = str(cargo_codigo)
        if cargo_str not in [
            str(CODIGO_PERFIL_DIRETOR),
            str(CODIGO_PERFIL_ASSISTENTE_DIRECAO),
            str(CODIGO_PERFIL_DRE),
            str(CODIGO_PERFIL_GIPE),
        ]:
            logger.info("[PERMISSION] Usuário %s com perfil não autorizado (%s)", request.user.username, cargo_str)
            return False

        logger.info("[PERMISSION] Acesso permitido para %s (perfil %s)", request.user.username, cargo_str)
        return True
 
    def has_object_permission(self, request, view, obj):

        if request.user is None or not getattr(request.user, "is_authenticated", False):
            logger.info("[PERMISSION] Usuário anônimo tentando acessar objeto %s", obj)
            return False
 
        cargo_codigo = getattr(request.user, "cargo_codigo", None)
        if cargo_codigo is None:
            logger.info("[PERMISSION] Usuário %s sem cargo definido", request.user.username)
            return False
 
        cargo_str = str(cargo_codigo)
        logger.info("[PERMISSION] Verificando permissão de objeto para %s (perfil %s)", request.user.username, cargo_str)

        action = getattr(view, 'action', None)
        if cargo_str in [str(CODIGO_PERFIL_DIRETOR), str(CODIGO_PERFIL_ASSISTENTE_DIRECAO)]:
            return self._check_diretor_permission(request, obj, action)
        
        elif cargo_str == str(CODIGO_PERFIL_DRE):
            return self._check_dre_permission(request, obj, action)
        
        elif cargo_str == str(CODIGO_PERFIL_GIPE):
            return self._check_gipe_permission(request, obj)

        logger.info("[PERMISSION] Perfil %s não reconhecido para usuário %s", cargo_str, request.user.username)
        return False
 
    def _check_diretor_permission(self, request, obj, action):
 
        user_unidade = getattr(request.user, "unidade_codigo_eol", None)
        obj_unidade = getattr(obj, "unidade_codigo_eol", None)

        if not user_unidade:
            logger.info("[PERMISSION] %s sem unidade_codigo_eol", request.user.username)
            return False

        if obj_unidade != user_unidade:
            logger.info("[PERMISSION] Intercorrência não pertence à unidade do diretor %s", request.user.username)
            return False
        
        if action in ['update', 'partial_update'] and user_unidade == obj_unidade:
            logger.info("[PERMISSION] Diretor/Assistente %s pode editar PUT na sua unidade", request.user.username)
            return True

        if request.method in SAFE_METHODS or request.method == "POST":
            logger.info("[PERMISSION] Diretor %s tem permissão de leitura/criação", request.user.username)
            return True
 
        if request.method in ["PUT", "PATCH", "DELETE"]:
            permitido = getattr(obj, "pode_ser_editado_por_diretor", False)
            logger.info("[PERMISSION] Diretor %s pode editar? %s", request.user.username, permitido)
            return permitido

        return False
 
    def _check_dre_permission(self, request, obj, action):
 
        user_dre = getattr(request.user, "unidade_codigo_eol", None)
        obj_dre = getattr(obj, "dre_codigo_eol", None)

        if not user_dre:
            logger.info("[PERMISSION] %s sem dre_codigo_eol", request.user.username)
            return False
 
        if obj_dre != user_dre:
            logger.info("[PERMISSION] Intercorrência não pertence à DRE do usuário %s", request.user.username)
            return False
        
        if action in ['update', 'partial_update'] and user_dre == obj_dre:
            logger.info("[PERMISSION] DRE %s pode editar PUT na sua DRE", request.user.username)
            return True

        if request.method in SAFE_METHODS:
            logger.info("[PERMISSION] DRE %s leitura permitida", request.user.username)
            return True
        
        if request.method in ["PUT", "PATCH"]:
            flag_dre = getattr(obj, "pode_ser_editado_por_dre", False)
            flag_diretor = getattr(obj, "pode_ser_editado_por_diretor", False)

            return flag_dre or flag_diretor

        return False
 
    def _check_gipe_permission(self, request, obj):

        if request.method in SAFE_METHODS:
            logger.info("[PERMISSION] GIPE %s leitura permitida", request.user.username)
            return True
        
        if request.method in ["PUT", "PATCH"]:

            flag_gipe = getattr(obj, "pode_ser_editado_por_gipe", False)
            flag_dre = getattr(obj, "pode_ser_editado_por_dre", False)
            flag_diretor = getattr(obj, "pode_ser_editado_por_diretor", False)

            return flag_gipe or flag_dre or flag_diretor

        return False