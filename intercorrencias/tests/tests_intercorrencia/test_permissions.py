import pytest
from unittest.mock import Mock, patch

from rest_framework.views import APIView
from config.settings import CODIGO_PERFIL_DIRETOR, CODIGO_PERFIL_DRE, CODIGO_PERFIL_GIPE

from intercorrencias.permissions import IntercorrenciaPermission
import intercorrencias.permissions as perms


@pytest.fixture
def view():
    return APIView()


@pytest.fixture
def req():
    r = Mock()
    r.method = "GET"
    return r


@pytest.fixture
def intercorrencia():
    obj = Mock()
    obj.unidade_codigo_eol = "001"
    obj.dre_codigo_eol = "DRE01"
    obj.status = "finalizado"
    obj.pode_ser_editado_por_diretor = True
    obj.pode_ser_editado_por_dre = True
    obj.pode_ser_editado_por_gipe = True
    return obj


@pytest.fixture
def permission():
    return IntercorrenciaPermission()


@pytest.fixture
def diretor_user():
    u = Mock()
    u.username = "diretor"
    u.is_authenticated = True
    u.cargo_codigo = CODIGO_PERFIL_DIRETOR
    u.unidade_codigo_eol = "001"
    return u


@pytest.fixture
def dre_user():
    u = Mock()
    u.username = "dre"
    u.is_authenticated = True
    u.cargo_codigo = CODIGO_PERFIL_DRE
    u.dre_codigo_eol = "DRE01"
    return u


@pytest.fixture
def gipe_user():
    u = Mock()
    u.username = "gipe"
    u.is_authenticated = True
    u.cargo_codigo = CODIGO_PERFIL_GIPE
    return u


@pytest.mark.django_db
class TestIntercorrenciaPermission:

    def test_has_permission_user_none(self, permission, req, view):
        req.user = None
        assert not permission.has_permission(req, view)

    def test_has_permission_cargo_none(self, permission, req, view):
        user = Mock()
        user.is_authenticated = True
        user.cargo_codigo = None
        req.user = user
        assert not permission.has_permission(req, view)

    def test_has_permission_cargo_invalido(self, permission, req, view):
        user = Mock()
        user.is_authenticated = True
        user.cargo_codigo = "INVALIDO"
        req.user = user
        assert not permission.has_permission(req, view)

    def test_has_permission_valido(self, permission, req, view, diretor_user):
        req.user = diretor_user
        assert permission.has_permission(req, view)

    def test_has_object_permission_user_none(self, permission, req, view, intercorrencia):
        req.user = None
        assert not permission.has_object_permission(req, view, intercorrencia)

    def test_has_object_permission_cargo_none(self, permission, req, view, intercorrencia):
        user = Mock()
        user.is_authenticated = True
        user.cargo_codigo = None
        req.user = user
        assert not permission.has_object_permission(req, view, intercorrencia)

    def test_has_object_permission_diretor(self, permission, req, view, diretor_user, intercorrencia):
        req.user = diretor_user
        assert permission.has_object_permission(req, view, intercorrencia)

    def test_has_object_permission_with_integer_codes(self, permission, req, view, intercorrencia, monkeypatch):
        """Ensure the permission dispatch still works when the imported profile codes are integers.

        This exercises the str() normalization in the permission implementation.
        """
        # patch the constants inside the permissions module to integers
        monkeypatch.setattr(perms, "CODIGO_PERFIL_DIRETOR", 10)
        monkeypatch.setattr(perms, "CODIGO_PERFIL_DRE", 20)
        monkeypatch.setattr(perms, "CODIGO_PERFIL_GIPE", 30)

        # Diretor integer-coded user
        u_dir = Mock()
        u_dir.username = "dir_int"
        u_dir.is_authenticated = True
        u_dir.cargo_codigo = 10
        u_dir.unidade_codigo_eol = intercorrencia.unidade_codigo_eol

        req.user = u_dir
        assert permission.has_object_permission(req, view, intercorrencia)

        # DRE integer-coded user
        u_dre = Mock()
        u_dre.username = "dre_int"
        u_dre.is_authenticated = True
        u_dre.cargo_codigo = 20
        u_dre.dre_codigo_eol = intercorrencia.dre_codigo_eol

        req.user = u_dre
        assert permission.has_object_permission(req, view, intercorrencia)

        # GIPE integer-coded user
        u_gipe = Mock()
        u_gipe.username = "gipe_int"
        u_gipe.is_authenticated = True
        u_gipe.cargo_codigo = 30

        req.user = u_gipe
        assert permission.has_object_permission(req, view, intercorrencia)

    def test_diretor_logger_warning(self, permission, req, diretor_user, intercorrencia):
        diretor_user.unidade_codigo_eol = None
        req.user = diretor_user
        with patch("intercorrencias.permissions.logger.warning") as mock_logger:
            assert not permission._check_diretor_permission(req, intercorrencia)
            mock_logger.assert_called_once()

    def test_diretor_unidade_diferente(self, permission, req, diretor_user, intercorrencia):
        intercorrencia.unidade_codigo_eol = "999"
        req.user = diretor_user
        assert not permission._check_diretor_permission(req, intercorrencia)

    def test_diretor_post_put_patch_delete(self, permission, req, diretor_user, intercorrencia):
        req.user = diretor_user
        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            req.method = method
            intercorrencia.pode_ser_editado_por_diretor = True
            assert permission._check_diretor_permission(req, intercorrencia)
            intercorrencia.pode_ser_editado_por_diretor = False
            if method in ["PUT", "PATCH", "DELETE"]:
                assert not permission._check_diretor_permission(req, intercorrencia)

    def test_diretor_metodo_nao_permitido(self, permission, req, diretor_user, intercorrencia):
        req.user = diretor_user
        req.method = "CONNECT"
        assert not permission._check_diretor_permission(req, intercorrencia)

    def test_dre_logger_warning(self, permission, req, dre_user, intercorrencia):
        dre_user.dre_codigo_eol = None
        req.user = dre_user
        with patch("intercorrencias.permissions.logger.warning") as mock_logger:
            assert not permission._check_dre_permission(req, intercorrencia)
            mock_logger.assert_called_once()

    def test_dre_status_em_preenchimento(self, permission, req, dre_user, intercorrencia):
        intercorrencia.status = "em_preenchimento_diretor"
        req.user = dre_user
        assert not permission._check_dre_permission(req, intercorrencia)

    def test_dre_dre_diferente(self, permission, req, dre_user, intercorrencia):
        intercorrencia.dre_codigo_eol = "OUTRA"
        req.user = dre_user
        assert not permission._check_dre_permission(req, intercorrencia)

    def test_dre_put_patch_safe(self, permission, req, dre_user, intercorrencia):
        req.user = dre_user
        for method in ["PUT", "PATCH", "GET"]:
            req.method = method
            intercorrencia.pode_ser_editado_por_dre = True
            assert permission._check_dre_permission(req, intercorrencia)
            intercorrencia.pode_ser_editado_por_dre = False
            if method in ["PUT", "PATCH"]:
                assert not permission._check_dre_permission(req, intercorrencia)

    def test_dre_metodo_nao_permitido(self, permission, req, dre_user, intercorrencia):
        req.user = dre_user
        req.method = "TRACE"
        assert not permission._check_dre_permission(req, intercorrencia)

    def test_gipe_status_bloqueado(self, permission, req, gipe_user, intercorrencia):
        for status in ["em_preenchimento_diretor", "enviado_para_dre", "em_analise_dre"]:
            intercorrencia.status = status
            req.user = gipe_user
            assert not permission._check_gipe_permission(req, intercorrencia)

    def test_gipe_put_patch_safe(self, permission, req, gipe_user, intercorrencia):
        req.user = gipe_user
        for method in ["PUT", "PATCH", "GET"]:
            req.method = method
            intercorrencia.status = "finalizado"
            intercorrencia.pode_ser_editado_por_gipe = True
            assert permission._check_gipe_permission(req, intercorrencia)
            intercorrencia.pode_ser_editado_por_gipe = False
            if method in ["PUT", "PATCH"]:
                assert not permission._check_gipe_permission(req, intercorrencia)

    def test_gipe_metodo_nao_permitido(self, permission, req, gipe_user, intercorrencia):
        req.user = gipe_user
        intercorrencia.status = "finalizado"
        req.method = "CONNECT"
        assert not permission._check_gipe_permission(req, intercorrencia)

    def test_has_object_permission_cargo_invalido(self, permission, req, view, intercorrencia):
        user = Mock()
        user.is_authenticated = True
        user.cargo_codigo = "INVALIDO"
        req.user = user
        assert not permission.has_object_permission(req, view, intercorrencia)