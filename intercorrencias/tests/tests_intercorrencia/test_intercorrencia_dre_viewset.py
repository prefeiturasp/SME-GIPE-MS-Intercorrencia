import pytest
import secrets
from unittest.mock import patch
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.api.views.intercorrencias_dre_viewset import IntercorrenciaDreViewSet


@pytest.mark.django_db
class TestIntercorrenciaDreViewSet:
    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def create_user(self, django_user_model):
        def _create(username, perfil_codigo, unidade_codigo_eol):
            pwd = secrets.token_urlsafe(16)
            user = django_user_model.objects.create_user(username=username)
            user.set_password(pwd)
            user.cargo_codigo = perfil_codigo
            user.unidade_codigo_eol = unidade_codigo_eol
            user.save()
            return user
        return _create

    @pytest.fixture
    def dre_user(self, create_user):
        return create_user("dre", "1", "DRE01")

    @pytest.fixture
    def intercorrencia_dre(self, dre_user):
        return Intercorrencia.objects.create(
            unidade_codigo_eol="200237",
            dre_codigo_eol=dre_user.unidade_codigo_eol,
            status="em_preenchimento_dre",
            data_ocorrencia=timezone.now(),
            user_username=dre_user.username,
            motivo_encerramento_dre="Encerramento teste",
        )

    def _api_call(self, client, user, method, url, data):
        client.force_authenticate(user=user)
        return client.put(url, data, format="json")

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_enviar_para_gipe_sucesso(self, mock_get_unidade, client, dre_user, intercorrencia_dre):
        client.force_authenticate(user=dre_user)
        mock_get_unidade.return_value = {"codigo_eol": "200237", "dre_codigo_eol": "DRE01"}

        url = f"/api-intercorrencias/v1/dre/{intercorrencia_dre.uuid}/enviar-para-gipe/"
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": dre_user.unidade_codigo_eol,
            "motivo_encerramento_dre": "Encerramento concluído com sucesso"
        }
        response = client.put(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["motivo_encerramento_dre"] == "Encerramento concluído com sucesso"

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_enviar_para_gipe_erro_validacao(self, mock_get_unidade, client, dre_user, intercorrencia_dre):
        client.force_authenticate(user=dre_user)
        mock_get_unidade.return_value = {"codigo_eol": "200237", "dre_codigo_eol": "DRE01"}

        url = f"/api-intercorrencias/v1/dre/{intercorrencia_dre.uuid}/enviar-para-gipe/"
        data = {
            "unidade_codigo_eol": "200237",
            "dre_codigo_eol": dre_user.unidade_codigo_eol,
            "motivo_encerramento_dre": ""
        }

        response = client.put(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "motivo_encerramento_dre" in str(response.data["detail"])

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_enviar_para_gipe_exception_generica(self, mock_get_unidade, client, dre_user, intercorrencia_dre):
        mock_get_unidade.return_value = {"codigo_eol": "200237", "dre_codigo_eol": "DRE01"}

        url = f"/api-intercorrencias/v1/dre/{intercorrencia_dre.uuid}/enviar-para-gipe/"
        data = {"motivo_encerramento_dre": "teste"}

        with patch.object(IntercorrenciaDreViewSet, "get_object", side_effect=Exception("Erro inesperado")):
            response = self._api_call(client, dre_user, "put", url, data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Erro inesperado" in str(response.data["detail"])
    
    def test_handle_validation_error_lista(self, dre_user):
        viewset = IntercorrenciaDreViewSet()
        viewset.request = type("Request", (), {"user": dre_user})()
        
        exc = ValidationError({"detail": ["Erro de validação único"]})
        response = viewset.handle_exception(exc)
        
        assert response.data["detail"] == "Erro de validação único"