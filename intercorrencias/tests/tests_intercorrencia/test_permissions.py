import pytest
from unittest.mock import Mock, patch

from rest_framework.views import APIView
from django.conf import settings
from config.settings import CODIGO_PERFIL_DIRETOR, CODIGO_PERFIL_DRE, CODIGO_PERFIL_GIPE

import intercorrencias.permissions as perms
from intercorrencias.permissions import IntercorrenciaPermission, IsInternalServiceRequest


@pytest.fixture
def view():
    v = APIView()
    v.action = None
    return v


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
def dre_user(intercorrencia):
    u = Mock()
    u.username = "dre"
    u.is_authenticated = True
    u.cargo_codigo = CODIGO_PERFIL_DRE
    u.unidade_codigo_eol = intercorrencia.dre_codigo_eol
    return u


@pytest.fixture
def gipe_user():
    u = Mock()
    u.username = "gipe"
    u.is_authenticated = True
    u.cargo_codigo = CODIGO_PERFIL_GIPE
    return u


@pytest.fixture
def internal_permission():
    return IsInternalServiceRequest()


@pytest.fixture
def internal_req():
    r = Mock()
    r.headers = {}
    r.META = {"REMOTE_ADDR": "127.0.0.1"}
    return r


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

    def test_has_object_permission_with_integer_codes(self, req, view, intercorrencia, monkeypatch):
        # patch constants antes de instanciar a permissão
        monkeypatch.setattr(perms, "CODIGO_PERFIL_DIRETOR", 10)
        monkeypatch.setattr(perms, "CODIGO_PERFIL_DRE", 20)
        monkeypatch.setattr(perms, "CODIGO_PERFIL_GIPE", 30)
        monkeypatch.setattr(perms, "CODIGO_PERFIL_ASSISTENTE_DIRECAO", 40)
        permission = IntercorrenciaPermission()

        # Diretor integer-coded
        u_dir = Mock()
        u_dir.username = "dir_int"
        u_dir.is_authenticated = True
        u_dir.cargo_codigo = 10
        u_dir.unidade_codigo_eol = intercorrencia.unidade_codigo_eol
        req.user = u_dir
        view.action = None
        assert permission.has_object_permission(req, view, intercorrencia)

        # Assistente integer-coded
        u_ass = Mock()
        u_ass.username = "ass_int"
        u_ass.is_authenticated = True
        u_ass.cargo_codigo = 40
        u_ass.unidade_codigo_eol = intercorrencia.unidade_codigo_eol
        req.user = u_ass
        view.action = None
        assert permission.has_object_permission(req, view, intercorrencia)

        # DRE integer-coded
        u_dre = Mock()
        u_dre.username = "dre_int"
        u_dre.is_authenticated = True
        u_dre.cargo_codigo = 20
        u_dre.unidade_codigo_eol = intercorrencia.dre_codigo_eol
        req.user = u_dre
        view.action = None
        assert permission.has_object_permission(req, view, intercorrencia)

        # GIPE integer-coded
        u_gipe = Mock()
        u_gipe.username = "gipe_int"
        u_gipe.is_authenticated = True
        u_gipe.cargo_codigo = 30
        req.user = u_gipe
        view.action = None
        assert permission.has_object_permission(req, view, intercorrencia)

    def test_diretor_logger_info(self, permission, req, diretor_user, intercorrencia, view):
        diretor_user.unidade_codigo_eol = None
        req.user = diretor_user
        view.action = "update"
        with patch("intercorrencias.permissions.logger.info") as mock_logger:
            assert not permission._check_diretor_permission(req, intercorrencia, view.action)
            mock_logger.assert_called()

    def test_diretor_unidade_diferente(self, permission, req, diretor_user, intercorrencia, view):
        intercorrencia.unidade_codigo_eol = "999"
        req.user = diretor_user
        view.action = "update"
        assert not permission._check_diretor_permission(req, intercorrencia, view.action)

    def test_diretor_put_mesma_unidade(self, permission, req, diretor_user, intercorrencia, view):
        req.user = diretor_user
        req.method = "PUT"
        intercorrencia.unidade_codigo_eol = diretor_user.unidade_codigo_eol
        view.action = "update"
        assert permission._check_diretor_permission(req, intercorrencia, view.action)

    def test_diretor_metodo_nao_permitido(self, permission, req, diretor_user, intercorrencia, view):
        req.user = diretor_user
        req.method = "CONNECT"
        view.action = None
        assert not permission._check_diretor_permission(req, intercorrencia, view.action)

    def test_dre_logger_info(self, permission, req, dre_user, intercorrencia, view):
        dre_user.unidade_codigo_eol = None
        req.user = dre_user
        view.action = "update"
        with patch("intercorrencias.permissions.logger.info") as mock_logger:
            assert not permission._check_dre_permission(req, intercorrencia, view.action)
            mock_logger.assert_called()

    def test_dre_status_em_preenchimento(self, permission, req, dre_user, intercorrencia, view):
        intercorrencia.status = "em_preenchimento_diretor"
        req.method = 'PUT'
        req.user = dre_user
        view.action = "update"
        assert permission._check_dre_permission(req, intercorrencia, view.action)

    def test_dre_dre_diferente(self, permission, req, dre_user, intercorrencia, view):
        intercorrencia.dre_codigo_eol = "OUTRA"
        req.user = dre_user
        view.action = "update"
        assert not permission._check_dre_permission(req, intercorrencia, view.action)

    def test_dre_put_mesma_dre(self, permission, req, dre_user, intercorrencia, view):
        req.user = dre_user
        req.method = "PUT"
        intercorrencia.dre_codigo_eol = dre_user.unidade_codigo_eol
        intercorrencia.pode_ser_editado_por_dre = False
        intercorrencia.pode_ser_editado_por_diretor = False
        view.action = "update"
        assert permission._check_dre_permission(req, intercorrencia, view.action)

    def test_dre_metodo_nao_permitido(self, permission, req, dre_user, intercorrencia, view):
        req.user = dre_user
        req.method = "TRACE"
        view.action = None
        assert not permission._check_dre_permission(req, intercorrencia, view.action)

    def test_gipe_status_bloqueado(self, permission, req, gipe_user, intercorrencia):
        req.user = gipe_user
        for method in ["PUT", "PATCH"]:
            req.method = method
            for status in ["em_preenchimento_diretor", "enviado_para_dre", "em_analise_dre"]:
                intercorrencia.status = status
                assert permission._check_gipe_permission(req, intercorrencia)

    def test_gipe_put_patch_safe(self, permission, req, gipe_user, intercorrencia):
        req.user = gipe_user
        for method in ["PUT", "PATCH", "GET"]:
            req.method = method
            intercorrencia.status = "finalizado"

            intercorrencia.pode_ser_editado_por_gipe = True
            assert permission._check_gipe_permission(req, intercorrencia)

            intercorrencia.pode_ser_editado_por_gipe = False
            intercorrencia.pode_ser_editado_por_dre = False
            intercorrencia.pode_ser_editado_por_diretor = False

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
        view.action = None
        assert not permission.has_object_permission(req, view, intercorrencia)


@pytest.mark.django_db
class TestIsInternalServiceRequest:

    def test_has_permission_missing_expected_token(self, internal_permission, internal_req, view, monkeypatch):
        internal_req.headers = {"X-Internal-Service-Token": "abc"}
        monkeypatch.setattr(settings, "INTERNAL_SERVICE_TOKEN", None, raising=False)

        with patch("intercorrencias.permissions.logger.warning") as mock_logger:
            assert not internal_permission.has_permission(internal_req, view)
            mock_logger.assert_called()

    def test_has_permission_token_invalido(self, internal_permission, internal_req, view, monkeypatch):
        internal_req.headers = {"X-Internal-Service-Token": "wrong"}
        monkeypatch.setattr(settings, "INTERNAL_SERVICE_TOKEN", "secret", raising=False)

        with patch("intercorrencias.permissions.logger.warning") as mock_logger:
            assert not internal_permission.has_permission(internal_req, view)
            mock_logger.assert_called()

    def test_has_permission_token_valido(self, internal_permission, internal_req, view, monkeypatch):
        internal_req.headers = {"X-Internal-Service-Token": "secret"}
        monkeypatch.setattr(settings, "INTERNAL_SERVICE_TOKEN", "secret", raising=False)

        assert internal_permission.has_permission(internal_req, view)
