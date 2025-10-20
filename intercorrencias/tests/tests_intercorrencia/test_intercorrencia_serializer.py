import pytest
from uuid import uuid4
from django.utils import timezone
from unittest.mock import patch, MagicMock

from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError

from intercorrencias.services.unidades_service import ExternalServiceError
from intercorrencias.api.serializers.intercorrencia_serializer import (
    IntercorrenciaSerializer,
    IntercorrenciaDiretorCompletoSerializer,
    IntercorrenciaSecaoInicialSerializer,
    IntercorrenciaFurtoRouboSerializer,
)
from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia


@pytest.mark.django_db
class TestIntercorrenciaSerializer:
    @pytest.fixture
    def intercorrencia_data(self):
        return {
            "data_ocorrencia": timezone.now(),
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
        request.user = MagicMock(unidade_codigo_eol="123")
        return request

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_success(self, mock_get, intercorrencia_data, auth_request):
        mock_get.return_value = {"codigo_eol": "123", "dre_codigo_eol": "456"}
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
    def test_validate_unidade_nao_pertence_usuario(self, mock_get, intercorrencia_data, request_factory):
        request = request_factory.post("/fake-url/")
        request.user = MagicMock(unidade_codigo_eol="999")
        mock_get.return_value = {"codigo_eol": "123", "dre_codigo_eol": "456"}

        serializer = IntercorrenciaSerializer(
            data=intercorrencia_data, context={"request": request}
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

    def test_get_status_extra_method_returns_expected_label(self):
        intercorrencia = MagicMock(status="EM_PREENCHIMENTO")
        intercorrencia.STATUS_EXTRA_LABELS = {"EM_PREENCHIMENTO": "Em andamento"}
        serializer = IntercorrenciaSerializer()
        result = serializer.get_status_extra(intercorrencia)
        assert result == "Em andamento"

    @pytest.mark.django_db
    def test_diretor_completo_serializer_fields(self):
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="user",
            unidade_codigo_eol="123",
            dre_codigo_eol="456",
            sobre_furto_roubo_invasao_depredacao=True,
        )
        serializer = IntercorrenciaDiretorCompletoSerializer(intercorrencia)
        data = serializer.data
        assert "status_display" in data
        assert "status_extra" in data
        assert data["status_display"] == "Em preenchimento - Diretor"

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_secao_inicial_validate_success(self, mock_get, intercorrencia_data, auth_request):
        mock_get.return_value = {"codigo_eol": "123", "dre_codigo_eol": "456"}
        serializer = IntercorrenciaSecaoInicialSerializer(
            data=intercorrencia_data, context={"request": auth_request}
        )
        assert serializer.is_valid(), serializer.errors
        assert "uuid" not in serializer.validated_data
        assert "status" not in serializer.validated_data

    @pytest.mark.django_db
    def test_furto_roubo_validate_success(self):
        tipo = TipoOcorrencia.objects.create(nome=f"Furto {uuid4()}")
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="user",
            unidade_codigo_eol="123",
            dre_codigo_eol="456",
            sobre_furto_roubo_invasao_depredacao=True,
        )
        data = {
            "tipos_ocorrencia": [tipo.pk],
            "descricao_ocorrencia": "Roubo de equipamentos",
            "smart_sampa_situacao": "sim_com_dano",
        }
        serializer = IntercorrenciaFurtoRouboSerializer(
            instance=intercorrencia, data=data, partial=True
        )
        assert serializer.is_valid(), serializer.errors

    @pytest.mark.django_db
    def test_furto_roubo_validate_not_related(self):
        tipo = TipoOcorrencia.objects.create(nome=f"Furto {uuid4()}")
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="user",
            unidade_codigo_eol="123",
            dre_codigo_eol="456",
            sobre_furto_roubo_invasao_depredacao=False,
        )
        data = {
            "tipos_ocorrencia": [tipo.pk],
            "descricao_ocorrencia": "Roubo de equipamentos",
            "smart_sampa_situacao": "sim_com_dano",
        }
        serializer = IntercorrenciaFurtoRouboSerializer(
            instance=intercorrencia, data=data, partial=True
        )
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "não é sobre furto/roubo/invasão/depredação" in str(exc.value)

    @pytest.mark.django_db
    def test_furto_roubo_validate_campo_obrigatorio_vazio(self):
        tipo = TipoOcorrencia.objects.create(nome=f"Furto {uuid4()}")
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="user",
            unidade_codigo_eol="123",
            dre_codigo_eol="456",
            sobre_furto_roubo_invasao_depredacao=True,
            descricao_ocorrencia="",
            smart_sampa_situacao="sim_com_dano",
        )
        intercorrencia.tipos_ocorrencia.add(tipo)

        data = {
            "descricao_ocorrencia": "",
        }
        serializer = IntercorrenciaFurtoRouboSerializer(
            instance=intercorrencia, data=data, partial=True
        )
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "Este campo é obrigatório" in str(exc.value)