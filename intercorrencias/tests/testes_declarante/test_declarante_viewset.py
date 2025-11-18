import pytest
import secrets
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from intercorrencias.models.declarante import Declarante


@pytest.mark.django_db
class TestDeclaranteViewSet:

    @pytest.fixture
    def api_client(self, django_user_model):
        def _create(username="tester"):
            pwd = secrets.token_urlsafe(16)
            user = django_user_model.objects.create_user(username=username)
            user.set_password(pwd)
            user.save()
            client = APIClient()
            client.force_authenticate(user=user)
            return client
        return _create

    @pytest.fixture
    def declarantes(self):
        Declarante.objects.all().delete()
        ativo = Declarante.objects.create(declarante="Declarante Ativo", ativo=True)
        inativo = Declarante.objects.create(declarante="Declarante Inativo", ativo=False)
        return {"ativo": ativo, "inativo": inativo}

    def test_list_declarantes_ativos(self, api_client, declarantes):
        client = api_client()
        url = reverse("intercorrencia-declarante-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_200_OK
        results = response.json()

        assert len(results) == 1
        assert results[0]["declarante"] == declarantes["ativo"].declarante

    def test_list_requires_authentication(self):
        client = APIClient()
        url = reverse("intercorrencia-declarante-list")
        response = client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in response.data
    
    def test_ordering_by_declarante(self, api_client):
        client = api_client()
        d_zeta = Declarante.objects.create(declarante="Zeta", ativo=True)
        d_alpha = Declarante.objects.create(declarante="Alpha", ativo=True)

        url = reverse("intercorrencia-declarante-list")
        response = client.get(url)
        names = [item["declarante"] for item in response.json()]

        assert d_alpha.declarante in names
        assert d_zeta.declarante in names

        assert names.index(d_alpha.declarante) < names.index(d_zeta.declarante)

    def test_serializer_fields(self, api_client, declarantes):
        client = api_client()
        url = reverse("intercorrencia-declarante-list")
        response = client.get(url)
        result = response.json()[0]

        expected_fields = {"uuid", "declarante"}
        assert expected_fields.issubset(result.keys())