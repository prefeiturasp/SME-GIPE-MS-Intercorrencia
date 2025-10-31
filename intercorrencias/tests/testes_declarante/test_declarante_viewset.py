import pytest
import secrets
from django.urls import reverse
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.test import APIClient

from intercorrencias.models.declarante import Declarante


@pytest.mark.django_db
class TestDeclaranteViewSet:

    @pytest.fixture
    def api_client(self):
        pwd = secrets.token_urlsafe(16)
        user = User.objects.create_user(username="tester", password=pwd)
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    @pytest.fixture
    def declarantes(self):
        Declarante.objects.all().delete()
        ativo = Declarante.objects.create(declarante="Declarante Ativo", ativo=True)
        inativo = Declarante.objects.create(declarante="Declarante Inativo", ativo=False)
        return {"ativo": ativo, "inativo": inativo}

    def test_list_declarantes_ativos(self, api_client, declarantes):
        url = reverse("intercorrencia-declarante-list")
        response = api_client.get(url)

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
        Declarante.objects.create(declarante="Zeta", ativo=True)
        Declarante.objects.create(declarante="Alpha", ativo=True)

        url = reverse("intercorrencia-declarante-list")
        response = api_client.get(url)
        names = [item["declarante"] for item in response.json()]

        assert names == sorted(names)

    def test_serializer_fields(self, api_client, declarantes):
        url = reverse("intercorrencia-declarante-list")
        response = api_client.get(url)
        result = response.json()[0]

        expected_fields = {"uuid", "declarante"}
        assert expected_fields.issubset(result.keys())