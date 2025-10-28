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


@pytest.fixture
def intercorrencia_data():
    return {
        "data_ocorrencia": timezone.now(),
        "unidade_codigo_eol": "123",
        "dre_codigo_eol": "456",
        "user_username": "diretor1",
        "sobre_furto_roubo_invasao_depredacao": True,
    }


@pytest.fixture
def request_factory():
    return APIRequestFactory()


@pytest.fixture
def auth_request(request_factory):
    request = request_factory.post("/fake-url/")
    request.META['HTTP_AUTHORIZATION'] = "Bearer valid_token"
    request.user = MagicMock(unidade_codigo_eol="123")
    return request


@pytest.mark.django_db
class TestIntercorrenciaSerializerBase:
    """Testes do serializer principal IntercorrenciaSerializer"""

    class IntercorrenciaSerializerTest(IntercorrenciaSerializer):
        class Meta:
            model = Intercorrencia
            fields = "__all__"

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_success(self, mock_get, intercorrencia_data, auth_request):
        mock_get.return_value = {"codigo_eol": "123", "dre_codigo_eol": "456"}
        serializer = self.IntercorrenciaSerializerTest(
            data=intercorrencia_data, context={"request": auth_request}
        )
        assert serializer.is_valid(), serializer.errors

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_unidade_nao_encontrada(self, mock_get, intercorrencia_data, auth_request):
        mock_get.return_value = None
        serializer = self.IntercorrenciaSerializerTest(
            data=intercorrencia_data, context={"request": auth_request}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_dre_incorreta(self, mock_get, intercorrencia_data, auth_request):
        mock_get.return_value = {"codigo_eol": "123", "dre_codigo_eol": "999"}
        serializer = self.IntercorrenciaSerializerTest(
            data=intercorrencia_data, context={"request": auth_request}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_unidade_nao_pertence_usuario(self, mock_get, intercorrencia_data, request_factory):
        request = request_factory.post("/fake-url/")
        request.user = MagicMock(unidade_codigo_eol="999")
        mock_get.return_value = {"codigo_eol": "123", "dre_codigo_eol": "456"}

        serializer = self.IntercorrenciaSerializerTest(
            data=intercorrencia_data, context={"request": request}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_external_service_error(self, mock_get, intercorrencia_data, auth_request):
        mock_get.side_effect = ExternalServiceError("Erro externo")
        serializer = self.IntercorrenciaSerializerTest(
            data=intercorrencia_data, context={"request": auth_request}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_dre_fallback_dict(self, mock_get, intercorrencia_data, auth_request):
        mock_get.return_value = {"codigo_eol": "123", "dre": {"codigo_eol": "456"}}
        serializer = self.IntercorrenciaSerializerTest(
            data=intercorrencia_data, context={"request": auth_request}
        )
        assert serializer.is_valid(), serializer.errors

    def test_get_status_extra_method_returns_expected_label(self):
        intercorrencia = MagicMock(status="EM_PREENCHIMENTO")
        intercorrencia.STATUS_EXTRA_LABELS = {"EM_PREENCHIMENTO": "Em andamento"}
        serializer = IntercorrenciaSerializer()
        result = serializer.get_status_extra(intercorrencia)
        assert result == "Em andamento"


@pytest.mark.django_db
class TestIntercorrenciaDiretorCompletoSerializer:
    """Testes do serializer completo do Diretor"""

    def test_get_status_extra_method(self):
        intercorrencia = MagicMock(status="FINALIZADO")
        intercorrencia.STATUS_EXTRA_LABELS = {"FINALIZADO": "Concluído"}
        serializer = IntercorrenciaDiretorCompletoSerializer()
        assert serializer.get_status_extra(intercorrencia) == "Concluído"

    def test_serializer_fields(self):
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


@pytest.mark.django_db
class TestIntercorrenciaSecaoInicialSerializer:
    """Testes do serializer da seção inicial (Diretor)"""

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_success(self, mock_get, intercorrencia_data, auth_request):
        mock_get.return_value = {"codigo_eol": "123", "dre_codigo_eol": "456"}
        serializer = IntercorrenciaSecaoInicialSerializer(
            data=intercorrencia_data, context={"request": auth_request}
        )
        assert serializer.is_valid(), serializer.errors

    def test_is_valid_error_format(self, intercorrencia_data, auth_request):
        intercorrencia_data["unidade_codigo_eol"] = ""
        serializer = IntercorrenciaSecaoInicialSerializer(
            data=intercorrencia_data, context={"request": auth_request}
        )
        is_valid = serializer.is_valid()
        assert not is_valid
        assert "detail" in serializer.errors

    def test_is_valid_raise_exception(self, intercorrencia_data, auth_request):
        intercorrencia_data["unidade_codigo_eol"] = ""
        serializer = IntercorrenciaSecaoInicialSerializer(
            data=intercorrencia_data, context={"request": auth_request}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
class TestIntercorrenciaFurtoRouboSerializer:
    """Testes do serializer de furto/roubo/invasão/depredação"""

    def test_validate_success(self):
        tipo = TipoOcorrencia.objects.create(nome=f"Furto {uuid4()}")
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="user",
            unidade_codigo_eol="123",
            dre_codigo_eol="456",
            sobre_furto_roubo_invasao_depredacao=True,
        )
        data = {
            "tipos_ocorrencia": [str(tipo.uuid)],
            "descricao_ocorrencia": "Roubo de equipamentos",
            "smart_sampa_situacao": "sim_com_dano",
        }
        serializer = IntercorrenciaFurtoRouboSerializer(
            instance=intercorrencia, data=data, partial=True
        )
        assert serializer.is_valid(), serializer.errors

    def test_validate_not_related(self):
        tipo = TipoOcorrencia.objects.create(nome=f"Furto {uuid4()}")
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="user",
            unidade_codigo_eol="123",
            dre_codigo_eol="456",
            sobre_furto_roubo_invasao_depredacao=False,
        )
        data = {
            "tipos_ocorrencia": [str(tipo.uuid)],
            "descricao_ocorrencia": "Roubo de equipamentos",
            "smart_sampa_situacao": "sim_com_dano",
        }
        serializer = IntercorrenciaFurtoRouboSerializer(
            instance=intercorrencia, data=data, partial=True
        )
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "não é sobre furto/roubo/invasão/depredação" in str(exc.value)

    def test_validate_campo_obrigatorio_vazio(self):
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

        data = {"descricao_ocorrencia": ""}
        serializer = IntercorrenciaFurtoRouboSerializer(
            instance=intercorrencia, data=data, partial=True
        )
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "descricao_ocorrencia" in str(exc.value)

    def test_validate_tipos_ocorrencia_valido(self):
        tipo = TipoOcorrencia.objects.create(nome=f"Roubo {uuid4()}")
        serializer = IntercorrenciaFurtoRouboSerializer()
        result = serializer.validate_tipos_ocorrencia([tipo])
        assert result == [tipo]

    def test_is_valid_error_format(self):
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="user",
            unidade_codigo_eol="123",
            dre_codigo_eol="456",
            sobre_furto_roubo_invasao_depredacao=True,
        )
        data = {"descricao_ocorrencia": ""}
        serializer = IntercorrenciaFurtoRouboSerializer(
            instance=intercorrencia, data=data, partial=True
        )
        is_valid = serializer.is_valid()
        assert not is_valid
        assert "detail" in serializer.errors

    def test_is_valid_raise_exception(self):
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="user",
            unidade_codigo_eol="123",
            dre_codigo_eol="456",
            sobre_furto_roubo_invasao_depredacao=True,
        )
        data = {"descricao_ocorrencia": ""}
        serializer = IntercorrenciaFurtoRouboSerializer(
            instance=intercorrencia, data=data, partial=True
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_validate_tipos_ocorrencia_vazio(self):
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="user",
            unidade_codigo_eol="123",
            dre_codigo_eol="456",
            sobre_furto_roubo_invasao_depredacao=True,
        )

        data = {
            "tipos_ocorrencia": [],
            "descricao_ocorrencia": "Roubo de equipamentos",
            "smart_sampa_situacao": "sim_com_dano",
        }

        serializer = IntercorrenciaFurtoRouboSerializer(
            instance=intercorrencia, data=data, partial=True
        )

        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)

        assert "Este campo é obrigatório" in str(exc.value)