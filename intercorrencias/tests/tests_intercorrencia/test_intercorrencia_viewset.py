import pytest
import secrets
from django.utils import timezone
from unittest.mock import PropertyMock, patch, Mock, MagicMock

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError

from intercorrencias.models.envolvido import Envolvido
from intercorrencias.models.declarante import Declarante
from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia

from intercorrencias.api.views.intercorrencias_viewset import IntercorrenciaDiretorViewSet

from django.conf import settings

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
        return create_user("diretor", settings.CODIGO_PERFIL_DIRETOR, "200237")

    @pytest.fixture
    def assistente_user(self, create_user):
        return create_user("assistente", settings.CODIGO_PERFIL_ASSISTENTE_DIRECAO, "200237")

    @pytest.fixture
    def dre_user(self, create_user):
        return create_user("dre", settings.CODIGO_PERFIL_DRE, "DRE01")

    @pytest.fixture
    def gipe_user(self, create_user):
        return create_user("gipe", settings.CODIGO_PERFIL_GIPE, "GIPE01")

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
    
    @pytest.fixture
    def envolvido(self):
        return [Envolvido.objects.create(perfil_dos_envolvidos=i) for i in range(1, 3)]
    
    @pytest.fixture
    def declarante(self):
        return Declarante.objects.create(declarante="Declarante Teste", ativo=True)

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

    def test_nao_furto_roubo_sucesso(self, client, diretor_user, intercorrencia, tipos_ocorrencia, envolvido):
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)
        intercorrencia.sobre_furto_roubo_invasao_depredacao = False
        intercorrencia.save()
        data = {"unidade_codigo_eol": "200237", "dre_codigo_eol": "108500", "tipos_ocorrencia": [str(t.uuid) for t in tipos_ocorrencia], "descricao_ocorrencia": "Teste", "tem_info_agressor_ou_vitima": "sim", "envolvido": str(envolvido[0].uuid)}
        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/nao-furto-roubo/"
        response = self._api_call(client, diretor_user, 'put', url, data)
        print(response.status_code)
        print(response.json())
        assert response.status_code == status.HTTP_200_OK

    def test_nao_furto_roubo_bloqueado(self, client, diretor_user, intercorrencia, tipos_ocorrencia, envolvido):
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=False)
        data = {"unidade_codigo_eol": "200237", "dre_codigo_eol": "108500", "tipos_ocorrencia": [str(t.uuid) for t in tipos_ocorrencia], "descricao_ocorrencia": "Teste", "tem_info_agressor_ou_vitima": "sim", "envolvido": str(envolvido[0].uuid)}
        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/nao-furto-roubo/"
        response = self._api_call(client, diretor_user, 'put', url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_nao_furto_roubo_nao_editavel_retorna_400(self, client, diretor_user, intercorrencia, tipos_ocorrencia, envolvido):
        client.force_authenticate(user=diretor_user)
        intercorrencia.sobre_furto_roubo_invasao_depredacao = False
        intercorrencia.save()
        
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=False)

        data = {"unidade_codigo_eol": "200237", "dre_codigo_eol": "108500",
                "tipos_ocorrencia": [str(t.uuid) for t in tipos_ocorrencia],
                "descricao_ocorrencia": "Teste", "tem_info_agressor_ou_vitima": "sim",
                "envolvido": str(envolvido[0].uuid)}

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/nao-furto-roubo/"
        
        response = self._api_call(client, diretor_user, 'put', url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "não tem permissão" in str(response.data["detail"]).lower()

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

        response = self._api_call(client, diretor_user, 'put', url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "não tem permissão" in str(response.data["detail"]).lower()

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
    
    def test_secao_final_update_sucesso(self, client, diretor_user, intercorrencia, declarante):
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
            "declarante": str(declarante.uuid),
            "comunicacao_seguranca_publica": "sim_gcm",
            "protocolo_acionado": "ameaca",
        }
        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/secao-final/"
        response = self._api_call(client, diretor_user, 'put', url, data)
        assert response.status_code == status.HTTP_200_OK
    
    def test_secao_final_intercorrencia_nao_editavel(self, client, diretor_user, intercorrencia, declarante):
        client.force_authenticate(user=diretor_user)
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=False)
        
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
            "declarante": str(declarante.uuid),
            "comunicacao_seguranca_publica": "sim_gcm",
            "protocolo_acionado": "ameaca",
        }
        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/secao-final/"

        response = self._api_call(client, diretor_user, 'put', url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "não tem permissão" in str(response.data["detail"]).lower()

    def test_secao_final_sem_unidade(self, client, diretor_user, intercorrencia, declarante):
        diretor_user.unidade_codigo_eol = None
        diretor_user.save()
        data = {
            "unidade_codigo_eol": "",
            "dre_codigo_eol": "",
            "declarante": str(declarante.uuid),
            "comunicacao_seguranca_publica": "sim_gcm",
            "protocolo_acionado": "ameaca",
        }
        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/secao-final/"
        response = self._api_call(client, diretor_user, 'put', url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "não tem permissão" in str(response.data["detail"]).lower()

    def test_secao_final_serializer_exception(self, client, diretor_user, intercorrencia, declarante):
        client.force_authenticate(user=diretor_user)
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)
        with patch("intercorrencias.api.views.intercorrencias_viewset.IntercorrenciaSecaoFinalSerializer") as MockSerializer:
            mock_instance = Mock()
            mock_instance.is_valid.side_effect = Exception("Erro no serializer da seção final")
            MockSerializer.return_value = mock_instance
            data = {
                "unidade_codigo_eol": "200237",
                "dre_codigo_eol": "108500",
                "declarante": str(declarante.uuid),
                "comunicacao_seguranca_publica": "sim_gcm",
                "protocolo_acionado": "ameaca",
            }
            url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/secao-final/"
            response = client.put(url, data, format="json")
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Erro no serializer da seção final" in str(response.data["detail"])
            MockSerializer.assert_called()

    def test_secao_final_generic_exception(self, client, diretor_user, intercorrencia, declarante):
        client.force_authenticate(user=diretor_user)
        with patch(
            "intercorrencias.api.views.intercorrencias_viewset.IntercorrenciaDiretorViewSet.get_object",
            side_effect=Exception("Erro inesperado na seção final"),
        ):
            url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/secao-final/"
            data = {
                "unidade_codigo_eol": "200237",
                "dre_codigo_eol": "108500",
                "declarante": str(declarante.uuid),
                "comunicacao_seguranca_publica": "sim_gcm",
                "protocolo_acionado": "ameaca",
            }
            response = client.put(url, data, format="json")
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Erro inesperado na seção final" in str(response.data["detail"])

    def test_categorias_disponiveis_sucesso(self, client, diretor_user):
        client.force_authenticate(user=diretor_user)

        mock_data = {
            "motivoocorrencia": ["bullying", "racismo"],
            "genero": ["homem_cis", "mulher_cis"]
        }

        with patch(
            "intercorrencias.api.views.intercorrencias_viewset.get_values_info_agressor_choices",
            return_value=mock_data
        ) as mock_get_values:
            response = client.get("/api-intercorrencias/v1/diretor/categorias-disponiveis/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data == mock_data
        mock_get_values.assert_called_once()
    
    def test_categorias_disponiveis_generic_exception(self, client, diretor_user):
        client.force_authenticate(user=diretor_user)

        with patch(
            "intercorrencias.api.views.intercorrencias_viewset.get_values_info_agressor_choices",
            side_effect=Exception("Erro inesperado ao buscar categorias disponíveis")
        ):
            url = "/api-intercorrencias/v1/diretor/categorias-disponiveis/"
            response = client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Erro inesperado ao buscar categorias disponíveis" in str(response.data["detail"])
        
    def test_enviar_para_dre_sucesso(self, client, diretor_user, intercorrencia, tipos_ocorrencia):
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)
        data = {"unidade_codigo_eol": "200237", "dre_codigo_eol": "108500", "motivo_encerramento_ue": "Encerramento teste",}
        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/enviar-para-dre/"
        response = self._api_call(client, diretor_user, 'put', url, data)
        assert response.status_code == status.HTTP_200_OK
        
    def test_enviar_para_dre_nao_editavel(self, client, diretor_user, intercorrencia, declarante):
        client.force_authenticate(user=diretor_user)
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=False)
        
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
            "motivo_encerramento_ue": "Encerramento teste"
        }
        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/enviar-para-dre/"
        
        response = self._api_call(client, diretor_user, 'put', url, data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "não tem permissão" in str(response.data["detail"]).lower()
        
    def test_envviar_para_dre_generic_exception(self, client, diretor_user, intercorrencia):
        client.force_authenticate(user=diretor_user)
        with patch(
            "intercorrencias.api.views.intercorrencias_viewset.IntercorrenciaDiretorViewSet.get_object",
            side_effect=Exception("Erro inesperado ao enviar para DRE"),
        ):
            url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/enviar-para-dre/"
            data = {
                "unidade_codigo_eol": "200237",
                "dre_codigo_eol": "108500",
                "motivo_encerramento_ue": "Encerramento teste"
            }
            response = client.put(url, data, format="json")
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Erro inesperado ao enviar para DRE" in str(response.data["detail"])

    def test_info_agressor_sucesso(self, client, diretor_user, intercorrencia):
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)
        intercorrencia.tem_info_agressor_ou_vitima = "sim"
        intercorrencia.save()

        data = {
            "nome_pessoa_agressora": "João Silva",
            "idade_pessoa_agressora": 15,
            "motivacao_ocorrencia": ["bullying"],
            "genero_pessoa_agressora": "homem_cis",
            "grupo_etnico_racial": "branco",
            "etapa_escolar": "fundamental_alfabetizacao",
            "frequencia_escolar": "regularizada",
            "interacao_ambiente_escolar": "participa normalmente",
            "redes_protecao_acompanhamento": "orientação escolar",
            "notificado_conselho_tutelar": True,
            "acompanhado_naapa": False,
            "cep": "12345678",
            "logradouro": "Rua das Flores",
            "numero_residencia": "123",
            "complemento": "",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "estado": "SP",
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
        }

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/info-agressor/"
        response = self._api_call(client, diretor_user, "put", url, data)

        assert response.status_code == status.HTTP_200_OK

    def test_info_agressor_bloqueado(self, client, diretor_user, intercorrencia):
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=False)
        intercorrencia.tem_info_agressor_ou_vitima = "sim"
        intercorrencia.save()

        data = {"motivo_ocorrencia": "bullying"}

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/info-agressor/"
        response = self._api_call(client, diretor_user, "put", url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_info_agressor_regra_tem_info_agressor_ou_vitima(self, client, diretor_user, intercorrencia):
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)
        intercorrencia.tem_info_agressor_ou_vitima = "nao"
        intercorrencia.save()

        data = {"motivo_ocorrencia": "bullying"}

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/info-agressor/"
        response = self._api_call(client, diretor_user, "put", url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Só é possível preencher informações" in response.data["detail"]

    def test_info_agressor_sem_unidade(self, client, diretor_user, intercorrencia):
        diretor_user.unidade_codigo_eol = None
        diretor_user.save()

        data = {"motivo_ocorrencia": "bullying"}

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/info-agressor/"
        response = self._api_call(client, diretor_user, "put", url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_info_agressor_serializer_exception(self, client, diretor_user, intercorrencia):
        client.force_authenticate(user=diretor_user)
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)
        intercorrencia.tem_info_agressor_ou_vitima = "sim"
        intercorrencia.save()

        with patch(
            "intercorrencias.api.views.intercorrencias_viewset.IntercorrenciaInfoAgressorSerializer"
        ) as MockSerializer:
            mock_instance = Mock()
            mock_instance.is_valid.side_effect = Exception("Erro no serializer info/agressor")
            MockSerializer.return_value = mock_instance

            data = {"motivo_ocorrencia": "bullying"}
            url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/info-agressor/"

            response = client.put(url, data, format="json")

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Erro no serializer info/agressor" in response.data["detail"]
            MockSerializer.assert_called()

    def test_info_agressor_generic_exception(self, client, diretor_user, intercorrencia):
        client.force_authenticate(user=diretor_user)

        with patch(
            "intercorrencias.api.views.intercorrencias_viewset.IntercorrenciaDiretorViewSet.get_object",
            side_effect=Exception("Erro inesperado info/agressor"),
        ):
            data = {"motivo_ocorrencia": "bullying"}
            url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/info-agressor/"

            response = client.put(url, data, format="json")

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Erro inesperado info/agressor" in response.data["detail"]
    
    def test_info_agressor_nao_editavel(self, client, diretor_user, intercorrencia):
        client.force_authenticate(user=diretor_user)
        intercorrencia.tem_info_agressor_ou_vitima = "sim"
        intercorrencia.save()
        
        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=False)

        data = {
            "nome_pessoa_agressora": "João Silva",
            "idade_pessoa_agressora": 15,
            "motivacao_ocorrencia": "bullying",
            "genero_pessoa_agressora": "homem_cis",
            "grupo_etnico_racial": "branco",
            "etapa_escolar": "fundamental_alfabetizacao",
            "frequencia_escolar": "regularizada",
            "interacao_ambiente_escolar": "participa normalmente",
            "redes_protecao_acompanhamento": "orientação escolar",
            "notificado_conselho_tutelar": True,
            "acompanhado_naapa": False,
            "cep": "12345678",
            "logradouro": "Rua das Flores",
            "numero_residencia": "123",
            "complemento": "",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "estado": "SP",
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
        }

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/info-agressor/"
        response = self._api_call(client, diretor_user, "put", url, data)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "não tem permissão" in str(response.data["detail"]).lower()
        

@pytest.mark.django_db
class TestIntercorrenciaDiretorViewSetUpdate:
    """Testes para o método update do IntercorrenciaDiretorViewSet"""

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
        return create_user("diretor", settings.CODIGO_PERFIL_DIRETOR, "200237")

    @pytest.fixture
    def create_intercorrencia(self, diretor_user):
        def _create(
            unidade_codigo_eol="200237",
            dre_codigo_eol="108500",
            status="em_preenchimento_diretor",
            user_username=None,
            furto_roubo=False,
            tem_info="",
        ):
            return Intercorrencia.objects.create(
                unidade_codigo_eol=unidade_codigo_eol,
                dre_codigo_eol=dre_codigo_eol,
                status=status,
                data_ocorrencia=timezone.now(),
                user_username=user_username or diretor_user.username,
                sobre_furto_roubo_invasao_depredacao=furto_roubo,
                tem_info_agressor_ou_vitima=tem_info,
            )
        return _create

    @pytest.fixture
    def intercorrencia_editavel(self, create_intercorrencia, diretor_user):
        return create_intercorrencia(user_username=diretor_user.username, furto_roubo=True)

    @pytest.fixture
    def tipos_ocorrencia(self):
        return [TipoOcorrencia.objects.create(nome=f"Tipo {i}") for i in range(1, 3)]

    @pytest.fixture
    def envolvido(self):
        return Envolvido.objects.create(perfil_dos_envolvidos=1)

    def test_update_sucesso_com_dados_validos(self, client, diretor_user, intercorrencia_editavel, tipos_ocorrencia):
        """Testa atualização bem-sucedida com dados válidos"""
        type(intercorrencia_editavel).pode_ser_editado_por_diretor = PropertyMock(return_value=True)

        client.force_authenticate(user=diretor_user)
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
            "data_ocorrencia": "2025-10-25T10:00:00-03:00",
            "tipos_ocorrencia": [str(t.uuid) for t in tipos_ocorrencia],
            "descricao_ocorrencia": "Descrição atualizada",
            "smart_sampa_situacao": "sim_com_dano",
        }

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia_editavel.uuid}/"
        response = client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "Descrição atualizada" in response.data["descricao_ocorrencia"]

    def test_update_limpa_campos_furto_roubo(self, client, diretor_user, create_intercorrencia, envolvido):
        """Testa que campos de envolvido são limpos quando sobre_furto_roubo=True"""
        intercorrencia = create_intercorrencia(furto_roubo=False, tem_info="sim")
        intercorrencia.envolvido = envolvido
        intercorrencia.nome_pessoa_agressora = "João Silva"
        intercorrencia.save()

        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)

        client.force_authenticate(user=diretor_user)
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
            "sobre_furto_roubo_invasao_depredacao": True,
            "smart_sampa_situacao": "sim_com_dano",
        }

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/"
        response = client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        
        intercorrencia.refresh_from_db()
        assert intercorrencia.envolvido is None
        assert intercorrencia.tem_info_agressor_ou_vitima == ""
        assert intercorrencia.nome_pessoa_agressora == ""

    def test_update_limpa_smart_sampa_quando_nao_furto_roubo(self, client, diretor_user, intercorrencia_editavel):
        """Testa que smart_sampa_situacao é limpo quando sobre_furto_roubo=False"""
        intercorrencia_editavel.smart_sampa_situacao = "sim_com_dano"
        intercorrencia_editavel.save()

        type(intercorrencia_editavel).pode_ser_editado_por_diretor = PropertyMock(return_value=True)

        client.force_authenticate(user=diretor_user)
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
            "sobre_furto_roubo_invasao_depredacao": False,
        }

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia_editavel.uuid}/"
        response = client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        
        intercorrencia_editavel.refresh_from_db()
        assert intercorrencia_editavel.smart_sampa_situacao == ""

    def test_update_limpa_campos_agressor_quando_tem_info_nao(self, client, diretor_user, create_intercorrencia):
        """Testa que campos de agressor são limpos quando tem_info_agressor_ou_vitima != 'sim'"""
        intercorrencia = create_intercorrencia(furto_roubo=False, tem_info="sim")
        intercorrencia.nome_pessoa_agressora = "Maria Santos"
        intercorrencia.idade_pessoa_agressora = 16
        intercorrencia.motivacao_ocorrencia = ["bullying"]
        intercorrencia.save()

        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)

        client.force_authenticate(user=diretor_user)
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
            "tem_info_agressor_ou_vitima": "nao",
        }

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/"
        response = client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        
        intercorrencia.refresh_from_db()
        assert intercorrencia.nome_pessoa_agressora == ""
        assert intercorrencia.idade_pessoa_agressora is None
        assert intercorrencia.motivacao_ocorrencia == []

    def test_update_mantem_campos_agressor_quando_tem_info_sim(self, client, diretor_user, create_intercorrencia):
        """Testa que campos de agressor são mantidos quando tem_info_agressor_ou_vitima = 'sim'"""
        intercorrencia = create_intercorrencia(furto_roubo=False, tem_info="sim")
        intercorrencia.nome_pessoa_agressora = "Pedro Oliveira"
        intercorrencia.idade_pessoa_agressora = 17
        intercorrencia.motivacao_ocorrencia = ["violencia_fisica"]
        intercorrencia.save()

        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)

        client.force_authenticate(user=diretor_user)
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
            "tem_info_agressor_ou_vitima": "sim",
            "descricao_ocorrencia": "Descrição atualizada",
        }

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/"
        response = client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        
        intercorrencia.refresh_from_db()
        assert intercorrencia.nome_pessoa_agressora == "Pedro Oliveira"
        assert intercorrencia.idade_pessoa_agressora == 17
        assert intercorrencia.motivacao_ocorrencia == ["violencia_fisica"]

    def test_update_partial_true_permite_atualizacao_parcial(self, client, diretor_user, intercorrencia_editavel):
        """Testa que partial=True permite atualização de apenas alguns campos"""
        descricao_original = "Descrição original"
        intercorrencia_editavel.descricao_ocorrencia = descricao_original
        # Como a intercorrencia_editavel foi criada com sobre_furto_roubo=True,
        # o smart_sampa_situacao é válido. Vamos garantir que ela não seja limpa
        intercorrencia_editavel.smart_sampa_situacao = "sim_com_dano"
        intercorrencia_editavel.save()

        type(intercorrencia_editavel).pode_ser_editado_por_diretor = PropertyMock(return_value=True)

        client.force_authenticate(user=diretor_user)
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
            "descricao_ocorrencia": "Nova descrição",
        }

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia_editavel.uuid}/"
        response = client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        
        intercorrencia_editavel.refresh_from_db()
        assert intercorrencia_editavel.descricao_ocorrencia == "Nova descrição"
        # smart_sampa_situacao deve permanecer inalterado
        assert intercorrencia_editavel.smart_sampa_situacao == "sim_com_dano"

    def test_update_atualiza_timestamp(self, client, diretor_user, intercorrencia_editavel):
        """Testa que atualizado_em é atualizado corretamente"""
        timestamp_antigo = intercorrencia_editavel.atualizado_em

        type(intercorrencia_editavel).pode_ser_editado_por_diretor = PropertyMock(return_value=True)

        client.force_authenticate(user=diretor_user)
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
            "descricao_ocorrencia": "Nova descrição"
        }

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia_editavel.uuid}/"
        response = client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        
        intercorrencia_editavel.refresh_from_db()
        assert intercorrencia_editavel.atualizado_em > timestamp_antigo

    def test_update_retorna_serializer_completo(self, client, diretor_user, intercorrencia_editavel):
        """Testa que a resposta usa IntercorrenciaDiretorCompletoSerializer"""
        type(intercorrencia_editavel).pode_ser_editado_por_diretor = PropertyMock(return_value=True)

        client.force_authenticate(user=diretor_user)
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
            "descricao_ocorrencia": "Teste de resposta completa"
        }

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia_editavel.uuid}/"
        response = client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        # Verifica se campos do serializer completo estão presentes
        assert "uuid" in response.data
        assert "status_display" in response.data
        assert "criado_em" in response.data

    def test_update_com_dados_invalidos(self, client, diretor_user, intercorrencia_editavel):
        """Testa que dados inválidos retornam erro 400"""
        type(intercorrencia_editavel).pode_ser_editado_por_diretor = PropertyMock(return_value=True)

        client.force_authenticate(user=diretor_user)
        data = {
            "unidade_codigo_eol": "999999",  # Unidade inválida
            "dre_codigo_eol": "999999",
        }

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia_editavel.uuid}/"
        response = client.put(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_sem_autenticacao(self, client, intercorrencia_editavel):
        """Testa que requisição sem autenticação retorna erro 401"""
        data = {"descricao_ocorrencia": "Tentativa sem autenticação"}

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia_editavel.uuid}/"
        response = client.put(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_intercorrencia_inexistente(self, client, diretor_user):
        """Testa que intercorrência inexistente retorna erro 404"""
        client.force_authenticate(user=diretor_user)
        data = {"descricao_ocorrencia": "Teste"}

        uuid_invalido = "00000000-0000-0000-0000-000000000000"
        url = f"/api-intercorrencias/v1/diretor/{uuid_invalido}/"
        response = client.put(url, data, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_generic_exception(self, client, diretor_user, intercorrencia_editavel):
        """Testa tratamento de exceção genérica"""
        client.force_authenticate(user=diretor_user)

        with patch(
            "intercorrencias.api.views.intercorrencias_viewset.IntercorrenciaDiretorViewSet.get_object",
            side_effect=Exception("Erro inesperado no update"),
        ):
            data = {"descricao_ocorrencia": "Teste de exceção"}
            url = f"/api-intercorrencias/v1/diretor/{intercorrencia_editavel.uuid}/"
            response = client.put(url, data, format="json")

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Erro inesperado no update" in str(response.data["detail"])

    def test_update_serializer_exception(self, client, diretor_user, intercorrencia_editavel):
        """Testa exceção durante validação do serializer"""
        type(intercorrencia_editavel).pode_ser_editado_por_diretor = PropertyMock(return_value=True)
        client.force_authenticate(user=diretor_user)

        with patch(
            "intercorrencias.api.views.intercorrencias_viewset.IntercorrenciaUpdateDiretorCompletoSerializer"
        ) as MockSerializer:
            mock_instance = Mock()
            mock_instance.is_valid.side_effect = Exception("Erro no serializer update")
            MockSerializer.return_value = mock_instance

            data = {"descricao_ocorrencia": "Teste"}
            url = f"/api-intercorrencias/v1/diretor/{intercorrencia_editavel.uuid}/"
            response = client.put(url, data, format="json")

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Erro no serializer update" in str(response.data["detail"])
            MockSerializer.assert_called()

    def test_update_limpa_todos_campos_agressor_quando_furto_roubo(
        self, client, diretor_user, create_intercorrencia
    ):
        """Testa que TODOS os 17 campos de agressor/vítima são limpos quando muda para furto/roubo"""
        intercorrencia = create_intercorrencia(furto_roubo=False, tem_info="sim")
        
        # Preenche todos os campos de agressor
        intercorrencia.nome_pessoa_agressora = "João Silva"
        intercorrencia.idade_pessoa_agressora = 15
        intercorrencia.motivacao_ocorrencia = ["bullying"]
        intercorrencia.genero_pessoa_agressora = "homem_cis"
        intercorrencia.grupo_etnico_racial = "branco"
        intercorrencia.etapa_escolar = "fundamental_alfabetizacao"
        intercorrencia.frequencia_escolar = "regularizada"
        intercorrencia.interacao_ambiente_escolar = "participa"
        intercorrencia.redes_protecao_acompanhamento = "orientação"
        intercorrencia.notificado_conselho_tutelar = True
        intercorrencia.acompanhado_naapa = True
        intercorrencia.cep = "12345678"
        intercorrencia.logradouro = "Rua das Flores"
        intercorrencia.numero_residencia = "123"
        intercorrencia.complemento = "Apto 1"
        intercorrencia.bairro = "Centro"
        intercorrencia.cidade = "São Paulo"
        intercorrencia.estado = "SP"
        intercorrencia.save()

        type(intercorrencia).pode_ser_editado_por_diretor = PropertyMock(return_value=True)

        client.force_authenticate(user=diretor_user)
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": "108500",
            "sobre_furto_roubo_invasao_depredacao": True,
            "smart_sampa_situacao": "sim_com_dano",
        }

        url = f"/api-intercorrencias/v1/diretor/{intercorrencia.uuid}/"
        response = client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        
        intercorrencia.refresh_from_db()
        # Verifica que TODOS os campos foram limpos
        assert intercorrencia.nome_pessoa_agressora == ""
        assert intercorrencia.idade_pessoa_agressora is None
        assert intercorrencia.motivacao_ocorrencia == []
        assert intercorrencia.genero_pessoa_agressora == ""
        assert intercorrencia.grupo_etnico_racial == ""
        assert intercorrencia.etapa_escolar == ""
        assert intercorrencia.frequencia_escolar == ""
        assert intercorrencia.interacao_ambiente_escolar == ""
        assert intercorrencia.redes_protecao_acompanhamento == ""
        assert intercorrencia.notificado_conselho_tutelar is None
        assert intercorrencia.acompanhado_naapa is None
        assert intercorrencia.cep == ""
        assert intercorrencia.logradouro == ""
        assert intercorrencia.numero_residencia == ""
        assert intercorrencia.complemento == ""
        assert intercorrencia.bairro == ""
        assert intercorrencia.cidade == ""
        assert intercorrencia.estado == ""

