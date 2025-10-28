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