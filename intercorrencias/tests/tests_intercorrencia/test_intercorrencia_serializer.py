import pytest
from unittest.mock import patch

from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError

from intercorrencias.services.unidades_service import ExternalServiceError
from intercorrencias.api.serializers.intercorrencia_serializer import IntercorrenciaSerializer

@pytest.mark.django_db
class TestIntercorrenciaSerializer:

    @pytest.fixture
    def intercorrencia_data(self):
        return {
            "data_ocorrencia": "2025-10-07",
            "unidade_codigo_eol": "123",
            "dre_codigo_eol": "456",
            "sobre_furto_roubo_invasao_depredacao": True,
        }

    @pytest.fixture
    def request_factory(self):
        return APIRequestFactory()

    @pytest.fixture
    def auth_request(self, request_factory):
        request = request_factory.post("/fake-url/")
        request.META['HTTP_AUTHORIZATION'] = "Bearer valid_token"
        return request

    @patch("intercorrencias.services.unidades_service.get_unidade")
    @patch("intercorrencias.services.unidades_service.validar_unidade_usuario")
    def test_validate_success(self, mock_validar, mock_get, intercorrencia_data, auth_request):
        mock_get.return_value = {"codigo_eol": "123", "dre_codigo_eol": "456"}
        mock_validar.return_value = {"detail": "A unidade pertence ao usuário."}

        serializer = IntercorrenciaSerializer(
            data=intercorrencia_data, context={"request": auth_request}
        )
        assert serializer.is_valid(), serializer.errors
        validated_data = serializer.validated_data
        assert validated_data["unidade_codigo_eol"] == "123"
        assert validated_data["dre_codigo_eol"] == "456"

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_unidade_nao_encontrada(self, mock_get, intercorrencia_data, auth_request):
        mock_get.return_value = None
        serializer = IntercorrenciaSerializer(
            data=intercorrencia_data, context={"request": auth_request}
        )
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "Unidade não encontrada." in str(exc.value)

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_dre_incorreta(self, mock_get, intercorrencia_data, auth_request):
        mock_get.return_value = {"codigo_eol": "123", "dre_codigo_eol": "999"}
        serializer = IntercorrenciaSerializer(
            data=intercorrencia_data, context={"request": auth_request}
        )
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "DRE informada não corresponde à DRE da unidade." in str(exc.value)

    @patch("intercorrencias.services.unidades_service.get_unidade")
    @patch("intercorrencias.services.unidades_service.validar_unidade_usuario")
    def test_validate_unidade_nao_pertence_usuario(self, mock_validar, mock_get, intercorrencia_data, auth_request):
        mock_get.return_value = {"codigo_eol": "123", "dre_codigo_eol": "456"}
        mock_validar.return_value = {"detail": "Unidade inválida."}
        serializer = IntercorrenciaSerializer(
            data=intercorrencia_data, context={"request": auth_request}
        )
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "A unidade não pertence ao usuário autenticado." in str(exc.value)

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_external_service_error(self, mock_get, intercorrencia_data, auth_request):
        mock_get.side_effect = ExternalServiceError("Erro externo")
        serializer = IntercorrenciaSerializer(
            data=intercorrencia_data, context={"request": auth_request}
        )
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "Erro externo" in str(exc.value)

    @patch("intercorrencias.services.unidades_service.get_unidade")
    @patch("intercorrencias.services.unidades_service.validar_unidade_usuario")
    def test_validate_external_error_validar_unidade(self, mock_validar, mock_get, intercorrencia_data, auth_request):
        mock_get.return_value = {"codigo_eol": "123", "dre_codigo_eol": "456"}
        mock_validar.side_effect = ExternalServiceError("Erro no validar_unidade_usuario")

        serializer = IntercorrenciaSerializer(
            data=intercorrencia_data, context={"request": auth_request}
        )

        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)

        assert "Erro no validar_unidade_usuario" in str(exc.value)