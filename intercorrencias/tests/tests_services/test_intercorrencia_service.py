import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import Timeout, HTTPError, RequestException

from intercorrencias.services.intercorrencia_service import IntercorrenciasService


@pytest.mark.django_db
class TestIntercorrenciasService:

    @patch("intercorrencias.services.intercorrencia_service.requests.post")
    def test_alerta_finalizacao_sucesso(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status.return_value = None

        mock_post.return_value = mock_response

        result = IntercorrenciasService.alerta_finalizacao_intercorrencia(
            username="teste",
            data_ocorrencia="2024-01-01",
            uuid_ocorrencia="uuid-123"
        )

        assert result == {"success": True}
        mock_post.assert_called_once()

    @patch("intercorrencias.services.intercorrencia_service.requests.post")
    def test_alerta_finalizacao_timeout(self, mock_post):
        mock_post.side_effect = Timeout()

        result = IntercorrenciasService.alerta_finalizacao_intercorrencia(
            username="teste",
            data_ocorrencia="2024-01-01",
            uuid_ocorrencia="uuid-123"
        )

        assert result == {"success": False, "error": "timeout"}

    @patch("intercorrencias.services.intercorrencia_service.requests.post")
    def test_alerta_finalizacao_http_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Erro interno"

        http_error = HTTPError(response=mock_response)

        mock_response.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_response

        result = IntercorrenciasService.alerta_finalizacao_intercorrencia(
            username="teste",
            data_ocorrencia="2024-01-01",
            uuid_ocorrencia="uuid-123"
        )

        assert result["success"] is False
        assert result["error"] == "http_error"
        assert result["status_code"] == 500

    @patch("intercorrencias.services.intercorrencia_service.requests.post")
    def test_alerta_finalizacao_http_error_sem_response(self, mock_post):
        http_error = HTTPError(response=None)

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = http_error

        mock_post.return_value = mock_response

        result = IntercorrenciasService.alerta_finalizacao_intercorrencia(
            username="teste",
            data_ocorrencia="2024-01-01",
            uuid_ocorrencia="uuid-123"
        )

        assert result == {
            "success": False,
            "error": "http_error",
            "status_code": None,
        }

    @patch("intercorrencias.services.intercorrencia_service.requests.post")
    def test_alerta_finalizacao_request_exception(self, mock_post):
        mock_post.side_effect = RequestException("Erro de conexão")

        result = IntercorrenciasService.alerta_finalizacao_intercorrencia(
            username="teste",
            data_ocorrencia="2024-01-01",
            uuid_ocorrencia="uuid-123"
        )

        assert result == {"success": False, "error": "connection_error"}

    @patch("intercorrencias.services.intercorrencia_service.requests.post")
    def test_alerta_finalizacao_exception_generica(self, mock_post):
        mock_post.side_effect = Exception("Erro inesperado")

        result = IntercorrenciasService.alerta_finalizacao_intercorrencia(
            username="teste",
            data_ocorrencia="2024-01-01",
            uuid_ocorrencia="uuid-123"
        )

        assert result == {"success": False, "error": "unexpected_error"}