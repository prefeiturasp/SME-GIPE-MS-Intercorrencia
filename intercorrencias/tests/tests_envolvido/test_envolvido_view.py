import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from intercorrencias.models.envolvido import Envolvido

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return APIClient()


def test_endpoint_require_authentication(client):
    """
    Sem autenticação deve retornar 403 (IsAuthenticated está ativo).
    """
    url = reverse("envolvido-list")
    response = client.get(url)
    assert response.status_code == 403


def test_listar_apenas_tipos_ativos(client, django_user_model):
    """
    Usuário autenticado vê apenas os tipos com ativo=True.
    """
    user = django_user_model.objects.create_user(username="u1")
    client.force_authenticate(user=user)

    Envolvido.objects.create(perfil_dos_envolvidos="Teste A", ativo=True)
    Envolvido.objects.create(perfil_dos_envolvidos="Teste B", ativo=False)
    Envolvido.objects.create(perfil_dos_envolvidos="Teste C", ativo=True)

    url = reverse("envolvido-list")
    response = client.get(url)

    assert response.status_code == 200
    data = response.json()
    nomes = [t["perfil_dos_envolvidos"] for t in data]

    assert "Teste A" in nomes
    assert "Teste C" in nomes
    assert "Teste B" not in nomes

