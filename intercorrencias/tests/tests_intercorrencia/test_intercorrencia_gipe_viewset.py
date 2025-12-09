import pytest
import secrets
from unittest.mock import patch
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.choices.gipe_choices import get_values_gipe_choices
from intercorrencias.api.views.intercorrencias_gipe_viewset import IntercorrenciaGipeViewSet


@pytest.mark.django_db
class TestIntercorrenciaGipeViewSet:

    @pytest.fixture
    def client(self):
        return APIClient()

    @pytest.fixture
    def create_user(self, django_user_model):
        def _create(username, perfil_codigo, unidade_codigo_eol):
            pwd = secrets.token_urlsafe(16)
            user = django_user_model.objects.create_user(username=username)
            user.set_password(pwd)
            user.cargo_codigo = perfil_codigo
            user.unidade_codigo_eol = unidade_codigo_eol
            user.save()
            return user
        return _create

    @pytest.fixture
    def user(self, create_user):
        return create_user("gipe", "0", "GIPE01")
    
    @pytest.fixture
    def intercorrencia(self, user):
        return Intercorrencia.objects.create(
            unidade_codigo_eol="200237",
            dre_codigo_eol=user.unidade_codigo_eol,
            status="em_preenchimento_gipe",
            data_ocorrencia=timezone.now(),
            user_username=user.username,
            motivo_encerramento_dre="Encerramento teste",
        )

    def test_categorias_disponiveis_sucesso(self, client, user):
        client.force_authenticate(user=user)

        expected_data = get_values_gipe_choices()

        with patch(
            "intercorrencias.api.views.intercorrencias_gipe_viewset.get_values_gipe_choices",
            return_value=expected_data,
        ):
            response = client.get("/api-intercorrencias/v1/gipe/categorias-disponiveis/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data == expected_data

    def test_categorias_disponiveis_erro_generico(self, client, user):
        client.force_authenticate(user=user)

        with patch(
            "intercorrencias.api.views.intercorrencias_gipe_viewset.get_values_gipe_choices",
            side_effect=Exception("Erro interno inesperado")
        ):
            response = client.get("/api-intercorrencias/v1/gipe/categorias-disponiveis/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Erro interno inesperado" in str(response.data["detail"])

    def test_handle_exception_validation_error_lista(self, user):
        viewset = IntercorrenciaGipeViewSet()
        viewset.request = type("Request", (), {"user": user})()

        exc = ValidationError({"detail": ["Mensagem única"]})
        response = viewset.handle_exception(exc)

        assert response.data["detail"] == "Mensagem única"

    def test_handle_exception_validation_error_normal(self, user):
        viewset = IntercorrenciaGipeViewSet()
        viewset.request = type("Request", (), {"user": user})()

        exc = ValidationError("Mensagem simples")
        response = viewset.handle_exception(exc)

        assert "Mensagem simples" in str(response.data)

    def test_handle_exception_response_none(self, user):
        viewset = IntercorrenciaGipeViewSet()
        viewset.request = type("Request", (), {"user": user})()

        exc = Exception("Falha total no tratamento")
        with patch(
            "intercorrencias.api.views.intercorrencias_gipe_viewset.exception_handler",
            return_value=None
        ):
            response = viewset.handle_exception(exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"] == "Falha total no tratamento"

    def test_handle_exception_response_dict(self, user):
        viewset = IntercorrenciaGipeViewSet()
        viewset.request = type("Request", (), {"user": user})()

        class FakeResponse(Response):
            pass

        response_mock = FakeResponse({"detail": ["Apenas uma mensagem"]}, status=400)

        with patch(
            "intercorrencias.api.views.intercorrencias_gipe_viewset.exception_handler",
            return_value=response_mock
        ):
            exc = ValidationError({"detail": ["Apenas uma mensagem"]})
            response = viewset.handle_exception(exc)

        assert response.data["detail"] == "Apenas uma mensagem"
        assert response.status_code == 400

    def test_retrieve_intercorrencia_sucesso(self, client, user, intercorrencia):
        client.force_authenticate(user=user)
        url = f"/api-intercorrencias/v1/gipe/{intercorrencia.uuid}/"
        response = client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["uuid"] == str(intercorrencia.uuid)