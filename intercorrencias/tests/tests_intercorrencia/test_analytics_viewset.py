import pytest
import secrets
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestAnalyticsViewSet:

    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def create_user(self, django_user_model):
        def _create(username, perfil_codigo):
            pwd = secrets.token_urlsafe(16)
            user = django_user_model.objects.create_user(username=username)
            user.set_password(pwd)
            user.cargo_codigo = perfil_codigo
            user.save()
            return user
        return _create

    @pytest.fixture
    def user_gipe(self, create_user):
        return create_user("gipe_user", "0")

    @pytest.fixture
    def user_nao_gipe(self, create_user):
        return create_user("outro_user", "1")

    def _api_call(self, client, user, data):
        client.force_authenticate(user=user)
        url = "/api-intercorrencias/v1/analytics/"
        return client.post(url, data, format="json")

    def test_analytics_sucesso(self, client, user_gipe):
        data = {"ano": 2026}

        with patch(
            "intercorrencias.services.analytics_service.AnalyticsService.execute_pipeline_json",
            return_value={"resultado": "ok"}
        ) as mock_execute:

            response = self._api_call(client, user_gipe, data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {"resultado": "ok"}
        mock_execute.assert_called_once_with(data)

    def test_analytics_usuario_nao_gipe(self, client, user_nao_gipe):
        data = {"ano": 2026}

        response = self._api_call(client, user_nao_gipe, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Apenas usuários do GIPE" in str(response.data)

    def test_analytics_nao_autenticado(self, client):
        url = "/api-intercorrencias/v1/analytics/"

        response = client.post(url, {"ano": 2026}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_analytics_erro_no_service(self, client, user_gipe):
        data = {"ano": 2026}

        with patch(
            "intercorrencias.services.analytics_service.AnalyticsService.execute_pipeline_json",
            side_effect=Exception("Erro interno inesperado")
        ):
            response = self._api_call(client, user_gipe, data)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Erro interno inesperado" in str(response.data["detail"])