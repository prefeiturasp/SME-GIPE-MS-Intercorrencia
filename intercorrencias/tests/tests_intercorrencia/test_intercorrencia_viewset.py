import pytest
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.api.views.intercorrencias_viewset import IntercorrenciaViewSet

@pytest.mark.django_db
class TestIntercorrenciaViewSet:

    @pytest.fixture
    def api_client(self, django_user_model):
        user = django_user_model.objects.create_user(username="user1", password="pass")
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    @pytest.fixture
    def intercorrencia(self, api_client):
        return Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            unidade_codigo_eol="123",
            dre_codigo_eol="456",
            sobre_furto_roubo_invasao_depredacao=True,
            user_username="user1"
        )

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.validar_unidade_usuario")
    def test_create_intercorrencia_success(self, mock_validar, mock_get, api_client):
        mock_get.return_value = {"codigo_eol": "123", "dre_codigo_eol": "456"}
        mock_validar.return_value = {"detail": "A unidade pertence ao usuário."}

        data = {
            "data_ocorrencia": timezone.now(),
            "unidade_codigo_eol": "123",
            "dre_codigo_eol": "456",
            "sobre_furto_roubo_invasao_depredacao": True
        }
        url = reverse("intercorrencia-list")
        response = api_client.post(url, data, format="json")
        assert response.status_code == 201
        assert response.data["user_username"] == "user1"

    def test_retrieve_intercorrencia(self, api_client, intercorrencia):
        url = reverse("intercorrencia-detail", args=[intercorrencia.uuid])
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["uuid"] == str(intercorrencia.uuid)

    def test_list_intercorrencias_no_filters(self, api_client, intercorrencia):
        url = reverse("intercorrencia-list")
        response = api_client.get(url)
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_list_intercorrencias_with_filters(self, api_client, intercorrencia):
        url = reverse("intercorrencia-list")
        response = api_client.get(url, {"unidade": "123", "dre": "456", "usuario": "user1"})
        assert response.status_code == 200
        assert len(response.data) == 1

        response = api_client.get(url, {"unidade": "999"})
        assert response.status_code == 200
        assert len(response.data) == 0

    def test_handle_exception_generic_error(self, api_client):
        view = IntercorrenciaViewSet()
        class DummyException(Exception): pass
        exc = DummyException("Erro inesperado")

        response = view.handle_exception(exc)
        assert isinstance(response, Response)
        assert response.status_code == 400
        assert response.data["detail"] == "Erro inesperado"

    def test_handle_exception_detail_list(self, api_client):
        view = IntercorrenciaViewSet()
        exc = ValidationError({"detail": ["mensagem"]})
        response = view.handle_exception(exc)
        assert response.data["detail"] == "mensagem"

    def test_list_intercorrencias_paginated(self, api_client, intercorrencia):
        url = reverse("intercorrencia-list")

        with patch("intercorrencias.api.views.intercorrencias_viewset.IntercorrenciaViewSet.paginate_queryset") as mock_paginate:
            with patch("intercorrencias.api.views.intercorrencias_viewset.IntercorrenciaViewSet.get_paginated_response") as mock_get_paginated:
                mock_paginate.return_value = [intercorrencia]
                mock_get_paginated.side_effect = lambda data: Response(data, status=200)

                response = api_client.get(url)
                assert response.status_code == 200
                assert response.data[0]["uuid"] == str(intercorrencia.uuid)