# tests/intercorrencias/services/test_unidades_service.py
import importlib
import pytest
import requests


class _FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        # 404 é tratado antes no código; aqui simulamos erro para outros 4xx/5xx
        if self.status_code >= 400 and self.status_code != 404:
            # usar a exceção real do requests (fica disponível pois não trocaremos o módulo)
            raise requests.HTTPError(f"HTTP {self.status_code}")


@pytest.mark.django_db
def test_get_unidade_ok_returns_dict(settings, monkeypatch, caplog):
    # Configura base URL com barra final para testarmos o rstrip("/")
    settings.UNIDADES_BASE_URL = "http://servico-unidades/api/v1/unidades/"
    import intercorrencias.services.unidades_service as svc
    importlib.reload(svc)

    def fake_get(url, timeout):
        # A URL final deve estar sem barra duplicada e terminar com "/<codigo>/"
        assert url == f"{svc.BASE}/123456/"
        assert abs(timeout - 3.0) < 1e-6
        return _FakeResponse(200, {"codigo_eol": "123456", "dre_codigo_eol": "654321"})

    # 🔧 Patch apenas da função get, mantendo o módulo requests real
    monkeypatch.setattr(svc.requests, "get", fake_get)

    with caplog.at_level("INFO"):
        data = svc.get_unidade("123456")

    assert data == {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
    assert any("Consultando unidade no serviço B:" in rec.message for rec in caplog.records)


@pytest.mark.django_db
def test_get_unidade_404_returns_none(settings, monkeypatch):
    settings.UNIDADES_BASE_URL = "http://servico-unidades/api/v1/unidades/"
    import intercorrencias.services.unidades_service as svc
    importlib.reload(svc)

    def fake_get(url, timeout):
        return _FakeResponse(404)

    monkeypatch.setattr(svc.requests, "get", fake_get)

    data = svc.get_unidade("999999")
    assert data is None


@pytest.mark.django_db
def test_get_unidade_http_500_raises_external_service_error(settings, monkeypatch):
    settings.UNIDADES_BASE_URL = "http://servico-unidades/api/v1/unidades/"
    import intercorrencias.services.unidades_service as svc
    importlib.reload(svc)

    def fake_get(url, timeout):
        return _FakeResponse(500)

    monkeypatch.setattr(svc.requests, "get", fake_get)

    with pytest.raises(svc.ExternalServiceError) as exc:
        svc.get_unidade("123456")
    assert "Falha ao consultar unidade:" in str(exc.value)


@pytest.mark.django_db
def test_get_unidade_timeout_raises_external_service_error(settings, monkeypatch):
    settings.UNIDADES_BASE_URL = "http://servico-unidades/api/v1/unidades/"
    import intercorrencias.services.unidades_service as svc
    importlib.reload(svc)

    def fake_get(url, timeout):
        # usa a Timeout real do requests; será capturada como RequestException
        raise requests.Timeout("tempo esgotado")

    monkeypatch.setattr(svc.requests, "get", fake_get)

    with pytest.raises(svc.ExternalServiceError) as exc:
        svc.get_unidade("123456")
    assert "Falha ao consultar unidade:" in str(exc.value)
    assert "tempo esgotado" in str(exc.value)


@pytest.mark.django_db
def test_base_usa_rstrip_barra_final(settings):
    settings.UNIDADES_BASE_URL = "http://host/base/com/barra/"
    import intercorrencias.services.unidades_service as svc
    importlib.reload(svc)

    assert svc.BASE == "http://host/base/com/barra"
    assert not svc.BASE.endswith("/")
