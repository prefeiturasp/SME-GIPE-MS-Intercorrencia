import pytest
from unittest.mock import Mock, patch

import requests

from intercorrencias.services.anexos_service import AnexosService


@pytest.fixture
def service_defaults(monkeypatch):
    monkeypatch.setattr(AnexosService, "BASE_URL", "https://anexos.test/api-anexos/v1")
    monkeypatch.setattr(AnexosService, "INTERNAL_TOKEN", "token-123")
    monkeypatch.setattr(AnexosService, "TIMEOUT", 5)


def _make_response(payload=None):
    response = Mock()
    response.json.return_value = payload or {}
    response.raise_for_status = Mock()
    return response


def test_deletar_anexos_intercorrencia_sucesso(service_defaults):
    response = _make_response({"total_anexos": 2, "anexos_com_erro": 0})

    with patch("intercorrencias.services.anexos_service.requests.post", return_value=response) as post_mock:
        result = AnexosService.deletar_anexos_intercorrencia("uuid-123")

    assert result["success"] is True
    assert result["data"]["total_anexos"] == 2
    assert result["error"] is None
    assert result["total_anexos"] == 2

    post_mock.assert_called_once()
    args, kwargs = post_mock.call_args
    assert args[0] == "https://anexos.test/api-anexos/v1/anexos/deletar-por-intercorrencia/"
    assert kwargs["json"] == {"intercorrencia_uuid": "uuid-123"}
    assert kwargs["headers"]["X-Internal-Service-Token"] == "token-123"
    assert kwargs["timeout"] == 5


def test_deletar_anexos_intercorrencia_timeout(service_defaults):
    with patch(
        "intercorrencias.services.anexos_service.requests.post",
        side_effect=requests.exceptions.Timeout,
    ):
        result = AnexosService.deletar_anexos_intercorrencia("uuid-123")

    assert result["success"] is False
    assert result["error_type"] == "TIMEOUT"


def test_deletar_anexos_intercorrencia_connection_error(service_defaults):
    with patch(
        "intercorrencias.services.anexos_service.requests.post",
        side_effect=requests.exceptions.ConnectionError("down"),
    ):
        result = AnexosService.deletar_anexos_intercorrencia("uuid-123")

    assert result["success"] is False
    assert result["error_type"] == "CONNECTION_ERROR"


def test_deletar_anexos_intercorrencia_http_error(service_defaults):
    response = _make_response({"detail": "invalid"})
    response.status_code = 500
    http_error = requests.exceptions.HTTPError(response=response)
    response.raise_for_status.side_effect = http_error

    with patch("intercorrencias.services.anexos_service.requests.post", return_value=response):
        result = AnexosService.deletar_anexos_intercorrencia("uuid-123")

    assert result["success"] is False
    assert result["error_type"] == "HTTP_500"
    assert "invalid" in result["error"]


def test_deletar_anexos_intercorrencia_http_error_json_falha(service_defaults, monkeypatch):
    class _FakeException:
        class HTTPError(Exception):
            pass

    response = _make_response()
    response.status_code = 500
    response.json.side_effect = _FakeException.HTTPError("json failure")
    http_error = requests.exceptions.HTTPError(response=response)
    response.raise_for_status.side_effect = http_error
    import intercorrencias.services.anexos_service as anexos_service
    monkeypatch.setattr(anexos_service, "Exception", _FakeException, raising=False)

    with patch("intercorrencias.services.anexos_service.requests.post", return_value=response):
        result = AnexosService.deletar_anexos_intercorrencia("uuid-123")

    assert result["success"] is False
    assert result["error_type"] == "HTTP_500"
    assert "Erro HTTP 500 ao deletar anexos." in result["error"]


def test_deletar_anexos_intercorrencia_request_exception(service_defaults):
    with patch(
        "intercorrencias.services.anexos_service.requests.post",
        side_effect=requests.exceptions.RequestException("boom"),
    ):
        result = AnexosService.deletar_anexos_intercorrencia("uuid-123")

    assert result["success"] is False
    assert result["error_type"] == "REQUEST_ERROR"


def test_deletar_anexos_intercorrencia_unexpected_error(service_defaults):
    with patch(
        "intercorrencias.services.anexos_service.requests.post",
        side_effect=ValueError("boom"),
    ):
        result = AnexosService.deletar_anexos_intercorrencia("uuid-123")

    assert result["success"] is False
    assert result["error_type"] == "UNEXPECTED_ERROR"
