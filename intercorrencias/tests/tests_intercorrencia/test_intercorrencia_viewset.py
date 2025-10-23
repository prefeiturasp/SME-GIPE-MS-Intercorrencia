import pytest
import secrets
from django.utils import timezone
from unittest.mock import PropertyMock, patch, Mock, MagicMock

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia
from intercorrencias.api.views.intercorrencias_viewset import IntercorrenciaDiretorViewSet

from config.settings import (
    CODIGO_PERFIL_DIRETOR,
    CODIGO_PERFIL_ASSISTENTE_DIRECAO,
    CODIGO_PERFIL_DRE,
    CODIGO_PERFIL_GIPE,
)

@pytest.fixture(autouse=True)
def mock_get_unidade():
    mock_data = {
        "200237": {"codigo_eol": "200237", "dre_codigo_eol": "108500"},
        "300100": {"codigo_eol": "300100", "dre_codigo_eol": "108600"},
        "108500": {"codigo_eol": "108500"},
        "108600": {"codigo_eol": "108600"},
        "DRE01": {"codigo_eol": "DRE01"},
        "GIPE01": {"codigo_eol": "GIPE01"},
    }

    def _mock_get(codigo_eol):
        return mock_data.get(codigo_eol, None)

    with patch('intercorrencias.services.unidades_service.get_unidade', side_effect=_mock_get):
        yield

@pytest.mark.django_db
class TestIntercorrenciaDiretorViewSet:
    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def create_user(self, django_user_model):
        def _create(username, cargo_codigo, unidade_codigo_eol):
            pwd = secrets.token_urlsafe(16)
            user = django_user_model.objects.create_user(username=username)
            user.set_password(pwd)
            user.cargo_codigo = cargo_codigo
            user.unidade_codigo_eol = unidade_codigo_eol
            user.save()
            return user
        return _create

    @pytest.fixture
    def diretor_user(self, create_user):
        return create_user("diretor", CODIGO_PERFIL_DIRETOR, "200237")

    @pytest.fixture
    def assistente_user(self, create_user):
        return create_user("assistente", CODIGO_PERFIL_ASSISTENTE_DIRECAO, "200237")

    @pytest.fixture
    def dre_user(self, create_user):
        return create_user("dre", CODIGO_PERFIL_DRE, "DRE01")

    @pytest.fixture
    def gipe_user(self, create_user):
        return create_user("gipe", CODIGO_PERFIL_GIPE, "GIPE01")

    @pytest.fixture
    def create_intercorrencia(self, diretor_user):
        def _create(unidade_codigo_eol="200237", dre_codigo_eol="108500", status="em_preenchimento_diretor", user_username=None, furto_roubo=False):
            return Intercorrencia.objects.create(
                unidade_codigo_eol=unidade_codigo_eol,
                dre_codigo_eol=dre_codigo_eol,
                status=status,
                data_ocorrencia=timezone.now(),
                user_username=user_username or diretor_user.username,
                sobre_furto_roubo_invasao_depredacao=furto_roubo,
            )
        return _create

    @pytest.fixture
    def intercorrencia(self, create_intercorrencia, diretor_user):
        return create_intercorrencia(user_username=diretor_user.username, furto_roubo=True)

    @pytest.fixture
    def intercorrencia_outra_unidade(self, create_intercorrencia):
        return create_intercorrencia(unidade_codigo_eol="300100", dre_codigo_eol="108600", user_username="outro_diretor")

    @pytest.fixture
    def intercorrencia_dre(self, create_intercorrencia, dre_user):
        return create_intercorrencia(dre_codigo_eol=dre_user.unidade_codigo_eol, user_username=dre_user.username, furto_roubo=True)

    @pytest.fixture
    def tipos_ocorrencia(self):
        return [TipoOcorrencia.objects.create(nome=f"Tipo {i}") for i in range(1, 3)]

    def _api_call(self, client, user, method, url, data):
        client.force_authenticate(user=user)
        if method.lower() == 'post':
            return client.post(url, data, format='json')
        return client.put(url, data, format='json')

    def test_queryset_diretor(self, diretor_user, intercorrencia):
        viewset = IntercorrenciaDiretorViewSet()
        viewset.request = type("Request", (), {"user": diretor_user})()
        qs = viewset.get_queryset()
        assert intercorrencia in qs
        assert all(i.unidade_codigo_eol == diretor_user.unidade_codigo_eol for i in qs)

    def test_queryset_assistente(self, assistente_user):
        interc = Intercorrencia.objects.create(
            unidade_codigo_eol=assistente_user.unidade_codigo_eol,
            dre_codigo_eol="108500",
            status="em_preenchimento_diretor",
            data_ocorrencia=timezone.now(),
            user_username=assistente_user.username,
        )
        viewset = IntercorrenciaDiretorViewSet()
        viewset.request = type("Request", (), {"user": assistente_user})()
        qs = viewset.get_queryset()
        assert interc in qs

    def test_queryset_dre_filtra(self, dre_user, intercorrencia_dre):
        viewset = IntercorrenciaDiretorViewSet()
        viewset.request = type("Request", (), {"user": dre_user})()
        qs = viewset.get_queryset()
        assert intercorrencia_dre in qs
        assert all(i.dre_codigo_eol == dre_user.unidade_codigo_eol for i in qs)

    def test_queryset_gipe_ve_todas(self, gipe_user, intercorrencia, intercorrencia_outra_unidade):
        viewset = IntercorrenciaDiretorViewSet()
        viewset.request = type("Request", (), {"user": gipe_user})()
        qs = viewset.get_queryset()
        assert intercorrencia in qs and intercorrencia_outra_unidade in qs

    def test_queryset_sem_unidade_retorna_vazio(self, diretor_user, dre_user):
        for user in (diretor_user, dre_user):
            user.unidade_codigo_eol = None
            user.save()
            viewset = IntercorrenciaDiretorViewSet()
            viewset.request = type("Request", (), {"user": user})()
            assert viewset.get_queryset().count() == 0

    def test_secao_inicial_create_success(self, client, diretor_user):
        data = {"data_ocorrencia": "2025-10-21T21:00:00-03:00", "unidade_codigo_eol": "200237", "dre_codigo_eol": "108500", "sobre_furto_roubo_invasao_depredacao": True}
        response = self._api_call(client, diretor_user, 'post', '/api-intercorrencias/v1/diretor/secao-inicial/', data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_secao_inicial_create_assistente(self, client, assistente_user):
        data = {"data_ocorrencia": "2025-10-21T21:00:00-03:00", "unidade_codigo_eol": "200237", "dre_codigo_eol": "108500", "sobre_furto_roubo_invasao_depredacao": True}
        response = self._api_call(client, assistente_user, 'post', '/api-intercorrencias/v1/diretor/secao-inicial/', data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_secao_inicial_create_dre_negado(self, client, dre_user):
        data = {"data_ocorrencia": "2025-10-21T21:00:00-03:00", "unidade_codigo_eol": "200237", "dre_codigo_eol": "108500", "sobre_furto_roubo_invasao_depredacao": True}
        response = self._api_call(client, dre_user, 'post', '/api-intercorrencias/v1/diretor/secao-inicial/', data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_secao_inicial_create_sem_unidade(self, client, diretor_user):
        diretor_user.unidade_codigo_eol = None
        diretor_user.save()
        data = {"data_ocorrencia": "2025-10-21T21:00:00-03:00", "unidade_codigo_eol": "", "dre_codigo_eol": "", "sobre_furto_roubo_invasao_depredacao": True}
        response = self._api_call(client, diretor_user, 'post', '/api-intercorrencias/v1/diretor/secao-inicial/', data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Usuário sem unidade cadastrada" in str(response.data['detail'])

    def test_secao_inicial_update_sucesso(self, client, diretor_user, intercorrencia):
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)
        data = {"data_ocorrencia": "2025-10-21T21:00:00-03:00", "unidade_codigo_eol": "200237", "dre_codigo_eol": "108500", "sobre_furto_roubo_invasao_depredacao": False}
        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/secao-inicial/"
        response = self._api_call(client, diretor_user, 'put', url, data)
        assert response.status_code == status.HTTP_200_OK

    def test_secao_inicial_update_sem_unidade(self, client, diretor_user, intercorrencia):
        diretor_user.unidade_codigo_eol = None
        diretor_user.save()
        data = {"data_ocorrencia": "2025-10-21T21:00:00-03:00"}
        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/secao-inicial/"
        response = self._api_call(client, diretor_user, 'put', url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_furto_roubo_sucesso(self, client, diretor_user, intercorrencia, tipos_ocorrencia):
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)
        data = {"unidade_codigo_eol": "200237", "dre_codigo_eol": "108500", "tipos_ocorrencia": [str(t.uuid) for t in tipos_ocorrencia], "descricao_ocorrencia": "Teste", "smart_sampa_situacao": "sim_com_dano"}
        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/furto-roubo/"
        response = self._api_call(client, diretor_user, 'put', url, data)
        assert response.status_code == status.HTTP_200_OK

    def test_furto_roubo_bloqueado(self, client, diretor_user, intercorrencia, tipos_ocorrencia):
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=False)
        data = {"unidade_codigo_eol": "200237", "dre_codigo_eol": "108500", "tipos_ocorrencia": [str(tipos_ocorrencia[0].uuid)], "descricao_ocorrencia": "Teste bloqueado", "smart_sampa_situacao": "sim_com_dano"}
        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/furto-roubo/"
        response = self._api_call(client, diretor_user, 'put', url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_secoes_update_raise_permission_denied_sem_unidade(self, diretor_user, intercorrencia):
        diretor_user.unidade_codigo_eol = None
        diretor_user.save()
        factory = APIRequestFactory()
        data = {"data_ocorrencia": "2025-10-21T21:00:00-03:00"}
        request = factory.put("/", data, format="json")
        request.user = diretor_user
        drf_request = Request(request)

        viewset = IntercorrenciaDiretorViewSet()
        viewset.request = drf_request
        viewset.kwargs = {"uuid": str(intercorrencia.uuid)}
        viewset.get_object = MagicMock(return_value=intercorrencia)

        response = viewset.secao_inicial_update(drf_request, uuid=str(intercorrencia.uuid))
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Usuário sem unidade vinculada" in str(response.data["detail"])

    def test_furto_roubo_nao_editavel_retorna_400(self, client, diretor_user, intercorrencia, tipos_ocorrencia):
        client.force_authenticate(user=diretor_user)
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=False)
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
            "tipos_ocorrencia": [str(t.uuid) for t in tipos_ocorrencia],
            "descricao_ocorrencia": "Teste bloqueado",
            "smart_sampa_situacao": "sim_com_dano",
        }
        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/furto-roubo/"

        with patch("intercorrencias.api.views.intercorrencias_viewset.IntercorrenciaDiretorViewSet.check_object_permissions", return_value=None):
            response = client.put(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "não pode mais ser editada" in response.data["detail"]

    def test_handle_exception_generic(self, diretor_user):
        viewset = IntercorrenciaDiretorViewSet()
        viewset.request = type("Request", (), {"user": diretor_user})()
        exc = Exception("Erro genérico")
        response = viewset.handle_exception(exc)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Erro genérico" in response.data['detail']

    def test_handle_validation_error_lista(self, diretor_user):
        viewset = IntercorrenciaDiretorViewSet()
        viewset.request = type("Request", (), {"user": diretor_user})()
        exc = ValidationError({"detail": ["Erro de validação único"]})
        response = viewset.handle_exception(exc)
        assert response.data['detail'] == "Erro de validação único"

    def test_secao_inicial_serializer_exception(self, client, diretor_user):
        client.force_authenticate(user=diretor_user)
        with patch("intercorrencias.api.views.intercorrencias_viewset.IntercorrenciaSecaoInicialSerializer") as MockSerializer:
            mock_instance = Mock()
            mock_instance.is_valid.side_effect = Exception("Erro no serializer")
            MockSerializer.return_value = mock_instance
            data = {"data_ocorrencia": "2025-10-21T21:00:00-03:00", "unidade_codigo_eol": "200237", "dre_codigo_eol": "108500", "sobre_furto_roubo_invasao_depredacao": True}
            response = self._api_call(client, diretor_user, 'post', '/api-intercorrencias/v1/diretor/secao-inicial/', data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Erro no serializer" in str(response.data['detail'])
            MockSerializer.assert_called()

    def test_secao_inicial_update_serializer_exception(self, client, diretor_user, intercorrencia):
        client.force_authenticate(user=diretor_user)
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)
        with patch("intercorrencias.api.views.intercorrencias_viewset.IntercorrenciaSecaoInicialSerializer") as MockSerializer:
            mock_instance = Mock()
            mock_instance.is_valid.side_effect = Exception("Erro no update")
            MockSerializer.return_value = mock_instance
            data = {"data_ocorrencia": "2025-10-21T21:00:00-03:00", "unidade_codigo_eol": "200237", "dre_codigo_eol": "108500", "sobre_furto_roubo_invasao_depredacao": False}
            url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/secao-inicial/"
            response = self._api_call(client, diretor_user, 'put', url, data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Erro no update" in str(response.data['detail'])
            MockSerializer.assert_called()

    def test_furto_roubo_serializer_exception(self, client, diretor_user, intercorrencia, tipos_ocorrencia):
        client.force_authenticate(user=diretor_user)
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)
        with patch("intercorrencias.api.views.intercorrencias_viewset.IntercorrenciaFurtoRouboSerializer") as MockSerializer:
            mock_instance = Mock()
            mock_instance.is_valid.side_effect = Exception("Erro no furto/roubo")
            MockSerializer.return_value = mock_instance
            data = {"unidade_codigo_eol": "200237", "dre_codigo_eol": "108500", "tipos_ocorrencia": [str(t.uuid) for t in tipos_ocorrencia], "descricao_ocorrencia": "Teste", "smart_sampa_situacao": "sim_com_dano"}
            url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/furto-roubo/"
            response = self._api_call(client, diretor_user, 'put', url, data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Erro no furto/roubo" in str(response.data['detail'])
            MockSerializer.assert_called()