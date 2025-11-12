import uuid
import pytest
from unittest.mock import patch
from django.urls import reverse
from django.http import Http404
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.api.views.verify_intercorrencia_viewset import VerifyIntercorrenciaViewSet
from config.settings import (
    CODIGO_PERFIL_DIRETOR,
    CODIGO_PERFIL_ASSISTENTE_DIRECAO,
    CODIGO_PERFIL_DRE,
    CODIGO_PERFIL_GIPE,
)


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def fake_user():
    user = type("FakeUser", (), {})()
    user.is_authenticated = True
    user.username = "teste_user"
    user.cargo_codigo = str(CODIGO_PERFIL_DIRETOR)
    user.unidade_codigo_eol = "1000"
    return user


@pytest.fixture
def intercorrencia(db):
    return Intercorrencia.objects.create(
        uuid=uuid.uuid4(),
        dre_codigo_eol="9999",
        user_username="diretor_user",
        data_ocorrencia=timezone.now(),
    )


@pytest.mark.django_db
class TestVerifyIntercorrenciaViewSet:

    def _perform_request(self, factory, user, intercorrencia_uuid):
        view = VerifyIntercorrenciaViewSet.as_view({"get": "retrieve"})
        url = reverse("verify-intercorrencia-detail", kwargs={"uuid": intercorrencia_uuid})
        request = factory.get(url)
        force_authenticate(request, user=user)
        return view(request, uuid=intercorrencia_uuid)

    def test_retrieve_success_for_diretor(self, factory, intercorrencia, fake_user):
        fake_user.cargo_codigo = str(CODIGO_PERFIL_DIRETOR)
        fake_user.username = intercorrencia.user_username

        response = self._perform_request(factory, fake_user, intercorrencia.uuid)

        assert response.status_code == status.HTTP_200_OK
        assert "uuid" in response.data

    def test_retrieve_not_found_returns_400(self, factory, fake_user):
        fake_user.cargo_codigo = str(CODIGO_PERFIL_DIRETOR)

        with patch(
            "intercorrencias.api.views.verify_intercorrencia_viewset.get_object_or_404",
            side_effect=Http404,
        ):
            response = self._perform_request(factory, fake_user, uuid.uuid4())

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "não existe" in response.data["detail"].lower()

    def test_retrieve_dre_invalid_access_returns_400(self, factory, intercorrencia, fake_user):
        fake_user.cargo_codigo = str(CODIGO_PERFIL_DRE)
        fake_user.unidade_codigo_eol = "9998"

        response = self._perform_request(factory, fake_user, intercorrencia.uuid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "dre" in response.data["detail"].lower()

    def test_retrieve_assistente_invalid_access_returns_400(self, factory, intercorrencia, fake_user):
        fake_user.cargo_codigo = str(CODIGO_PERFIL_ASSISTENTE_DIRECAO)
        fake_user.username = "teste_user2"

        response = self._perform_request(factory, fake_user, intercorrencia.uuid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "criadas por você" in response.data["detail"].lower()

    def test_retrieve_gipe_bypass_validations_returns_200(self, factory, intercorrencia, fake_user):
        fake_user.cargo_codigo = str(CODIGO_PERFIL_GIPE)

        response = self._perform_request(factory, fake_user, intercorrencia.uuid)

        assert response.status_code == status.HTTP_200_OK
        assert "uuid" in response.data

    def test_retrieve_invalid_profile_returns_400(self, factory, intercorrencia, fake_user):
        fake_user.cargo_codigo = "999999"

        response = self._perform_request(factory, fake_user, intercorrencia.uuid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "não autorizado" in response.data["detail"].lower()