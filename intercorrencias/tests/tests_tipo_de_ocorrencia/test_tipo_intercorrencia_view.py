import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def test_endpoint_require_authentication(client):
    """
    Sem autenticação deve retornar 403 (IsAuthenticated está ativo).
    """
    url = reverse("tipo-ocorrencia-list")
    response = client.get(url)
    assert response.status_code == 403

def test_filtrar_tipo_patrimonial_retorna_patrimonial_e_todos(
    client, django_user_model
):
    user = django_user_model.objects.create_user(username="u1")
    client.force_authenticate(user=user)

    TipoOcorrencia.objects.create(
        nome="Patrimonial 1",
        ativo=True,
        tipo_formulario="PATRIMONIAL",
    )

    TipoOcorrencia.objects.create(
        nome="Todos 1",
        ativo=True,
        tipo_formulario="TODOS",
    )

    TipoOcorrencia.objects.create(
        nome="Geral 1",
        ativo=True,
        tipo_formulario="GERAL",
    )

    url = reverse("tipo-ocorrencia-list")

    response = client.get(
        url,
        {"tipo_formulario": "PATRIMONIAL"}
    )

    assert response.status_code == 200

    data = response.json()
    nomes = [t["nome"] for t in data]

    assert "Patrimonial 1" in nomes
    assert "Todos 1" in nomes
    assert "Geral 1" not in nomes

def test_filtrar_tipo_geral_retorna_geral_e_todos(
    client, django_user_model
):
    user = django_user_model.objects.create_user(username="u2")
    client.force_authenticate(user=user)

    TipoOcorrencia.objects.create(
        nome="Geral 1",
        ativo=True,
        tipo_formulario="GERAL",
    )

    TipoOcorrencia.objects.create(
        nome="Todos 1",
        ativo=True,
        tipo_formulario="TODOS",
    )

    TipoOcorrencia.objects.create(
        nome="Patrimonial 1",
        ativo=True,
        tipo_formulario="PATRIMONIAL",
    )

    url = reverse("tipo-ocorrencia-list")

    response = client.get(
        url,
        {"tipo_formulario": "GERAL"}
    )

    assert response.status_code == 200

    data = response.json()
    nomes = [t["nome"] for t in data]

    assert "Geral 1" in nomes
    assert "Todos 1" in nomes
    assert "Patrimonial 1" not in nomes

def test_filtrar_tipo_invalido_retorna_vazio(
    client, django_user_model
):
    user = django_user_model.objects.create_user(username="u3")
    client.force_authenticate(user=user)

    TipoOcorrencia.objects.create(
        nome="TESTE_INVALIDO_A",
        ativo=True,
        tipo_formulario="GERAL",
    )

    TipoOcorrencia.objects.create(
        nome="TESTE_INVALIDO_B",
        ativo=True,
        tipo_formulario="TODOS",
    )

    TipoOcorrencia.objects.create(
        nome="TESTE_INVALIDO_C",
        ativo=True,
        tipo_formulario="PATRIMONIAL",
    )

    url = reverse("tipo-ocorrencia-list")

    response = client.get(
        url,
        {"tipo_formulario": "INVALIDO"}
    )

    assert response.status_code == 200

    data = response.json()
    assert data == []