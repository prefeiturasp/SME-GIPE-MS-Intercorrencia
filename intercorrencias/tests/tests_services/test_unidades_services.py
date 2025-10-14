import pytest
import requests
from unittest.mock import patch, MagicMock

from django.conf import settings

from intercorrencias.services import unidades_service
from intercorrencias.services.unidades_service import ExternalServiceError

@pytest.mark.django_db
class TestUnidadesService:

    @patch("intercorrencias.services.unidades_service.requests.get")
    def test_get_unidade_sucesso(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"codigo_eol": "123", "dre_codigo_eol": "456"}
        mock_get.return_value = mock_response

        result = unidades_service.get_unidade("123")
        assert result == {"codigo_eol": "123", "dre_codigo_eol": "456"}
        mock_get.assert_called_once_with(f"{settings.UNIDADES_BASE_URL.rstrip('/')}/123/", timeout=3.0)

    @patch("intercorrencias.services.unidades_service.requests.get")
    def test_get_unidade_404(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = unidades_service.get_unidade("123")
        assert result is None

    @patch("intercorrencias.services.unidades_service.requests.get")
    def test_get_unidade_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException("Erro de conexão")

        with pytest.raises(ExternalServiceError) as exc:
            unidades_service.get_unidade("123")
        assert "Falha ao consultar unidade" in str(exc.value)

    @patch("intercorrencias.services.unidades_service.requests.get")
    def test_validar_unidade_usuario_sucesso_200(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"detail": "A unidade pertence ao usuário."}
        mock_get.return_value = mock_response

        result = unidades_service.validar_unidade_usuario("123", "token123")
        assert result == {"detail": "A unidade pertence ao usuário."}
        mock_get.assert_called_once_with(
            f"{settings.UNIDADES_BASE_URL.rstrip('/')}/123/verificar-unidade/",
            headers={"Authorization": "Bearer token123", "Accept": "application/json"},
            timeout=3.0
        )

    @patch("intercorrencias.services.unidades_service.requests.get")
    def test_validar_unidade_usuario_sucesso_403(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {"detail": "Unidade não pertence."}
        mock_get.return_value = mock_response

        result = unidades_service.validar_unidade_usuario("123", "token123")
        assert result == {"detail": "Unidade não pertence."}

    @patch("intercorrencias.services.unidades_service.requests.get")
    def test_validar_unidade_usuario_outros_status(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = unidades_service.validar_unidade_usuario("123", "token123")
        assert result is None

    @patch("intercorrencias.services.unidades_service.requests.get")
    def test_validar_unidade_usuario_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException("Erro de conexão")
        with pytest.raises(ExternalServiceError) as exc:
            unidades_service.validar_unidade_usuario("123", "token123")
        assert "Falha ao validar unidade" in str(exc.value)