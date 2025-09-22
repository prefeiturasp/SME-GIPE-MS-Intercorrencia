import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework.pagination import PageNumberPagination

from intercorrencias.models.intercorrencia import Intercorrencia


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="tester",
        password="secret",
        email="tester@example.com"
    )


def _patch_unidades_service_ok(monkeypatch, dre_codigo="654321"):
    """
    Parcha o unidades_service usado dentro do serializer para o caminho feliz.
    """
    import intercorrencias.api.serializers.intercorrencia_serializer as mod

    class FakeExternalServiceError(Exception):
        pass

    def fake_get_unidade(codigo_unidade):
        return {"codigo_eol": codigo_unidade, "dre_codigo_eol": dre_codigo}

    monkeypatch.setattr(
        mod,
        "unidades_service",
        type("S", (), {
            "get_unidade": staticmethod(fake_get_unidade),
            "ExternalServiceError": FakeExternalServiceError
        })
    )


@pytest.mark.django_db
def test_auth_required_returns_401(api_client):
    url = reverse("intercorrencia-list")
    resp = api_client.get(url)
    assert resp.status_code == 403


@pytest.mark.django_db
def test_create_ok_sets_user_username(api_client, user, monkeypatch):
    _patch_unidades_service_ok(monkeypatch, dre_codigo="111111")

    api_client.force_authenticate(user=user)
    url = reverse("intercorrencia-list")

    payload = {
        "data_ocorrencia": timezone.now().isoformat(),
        "unidade_codigo_eol": "123456",
        "dre_codigo_eol": "111111",
        "sobre_furto_roubo_invasao_depredacao": True,
        # Mesmo se enviar, serializer ignora por ser read-only; perform_create define.
        "user_username": "ignorado_no_input",
    }

    resp = api_client.post(url, payload, format="json")
    assert resp.status_code == 201, resp.data

    # Verifica corpo e persistência
    data = resp.data
    assert data["unidade_codigo_eol"] == "123456"
    assert data["dre_codigo_eol"] == "111111"
    assert data["sobre_furto_roubo_invasao_depredacao"] is True
    assert data["user_username"] == user.username  # setado pelo perform_create

    obj = Intercorrencia.objects.get(uuid=data["uuid"])
    assert obj.user_username == user.username


@pytest.mark.django_db
def test_retrieve_by_uuid(api_client, user, intercorrencia_factory):
    api_client.force_authenticate(user=user)

    obj = intercorrencia_factory(
        unidade_codigo_eol="222222",
        dre_codigo_eol="333333",
        sobre_furto_roubo_invasao_depredacao=False,
    )

    url = reverse("intercorrencia-detail", kwargs={"uuid": str(obj.uuid)})
    resp = api_client.get(url)
    assert resp.status_code == 200
    assert resp.data["uuid"] == str(obj.uuid)
    assert resp.data["unidade_codigo_eol"] == "222222"


@pytest.mark.django_db
def test_list_sem_filtro(api_client, user, intercorrencia_factory):
    api_client.force_authenticate(user=user)

    intercorrencia_factory()
    intercorrencia_factory()
    intercorrencia_factory()

    url = reverse("intercorrencia-list")
    resp = api_client.get(url)
    assert resp.status_code == 200
    assert isinstance(resp.data, list)  # sem paginação configurada -> lista direta
    assert len(resp.data) == 3


@pytest.mark.django_db
def test_filter_por_unidade(api_client, user, intercorrencia_factory):
    api_client.force_authenticate(user=user)

    a = intercorrencia_factory(unidade_codigo_eol="999999")
    c = intercorrencia_factory(unidade_codigo_eol="999999")

    url = reverse("intercorrencia-list")
    resp = api_client.get(url, {"unidade": "999999"})
    assert resp.status_code == 200
    uuids = {item["uuid"] for item in resp.data}
    assert uuids == {str(a.uuid), str(c.uuid)}


@pytest.mark.django_db
def test_filter_por_dre(api_client, user, intercorrencia_factory):
    api_client.force_authenticate(user=user)

    a = intercorrencia_factory(dre_codigo_eol="123123")
    c = intercorrencia_factory(dre_codigo_eol="123123")

    url = reverse("intercorrencia-list")
    resp = api_client.get(url, {"dre": "123123"})
    assert resp.status_code == 200
    uuids = {item["uuid"] for item in resp.data}
    assert uuids == {str(a.uuid), str(c.uuid)}


@pytest.mark.django_db
def test_filter_por_usuario(api_client, user, intercorrencia_factory):
    api_client.force_authenticate(user=user)

    a = intercorrencia_factory(user_username="alice")
    c = intercorrencia_factory(user_username="alice")

    url = reverse("intercorrencia-list")
    resp = api_client.get(url, {"usuario": "alice"})
    assert resp.status_code == 200
    uuids = {item["uuid"] for item in resp.data}
    assert uuids == {str(a.uuid), str(c.uuid)}


@pytest.mark.django_db
def test_list_usando_paginacao(api_client, user, intercorrencia_factory, monkeypatch):
    # força paginação na viewset (independente do cache do DRF)
    import intercorrencias.api.views.intercorrencias_viewset as vs

    class SmallPage(PageNumberPagination):
        page_size = 2

    # injeta a paginação na classe da viewset
    monkeypatch.setattr(vs.IntercorrenciaViewSet, "pagination_class", SmallPage, raising=False)

    api_client.force_authenticate(user=user)

    # cria 3 registros -> primeira página terá 2
    for _ in range(3):
        intercorrencia_factory()

    url = reverse("intercorrencia-list")
    resp = api_client.get(url)

    assert resp.status_code == 200
    assert isinstance(resp.data, dict)        # agora é resposta paginada
    assert resp.data["count"] == 3
    assert len(resp.data["results"]) == 2
    assert resp.data["next"] is not None
