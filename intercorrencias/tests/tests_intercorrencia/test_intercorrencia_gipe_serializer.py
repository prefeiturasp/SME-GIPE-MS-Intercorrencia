import uuid
import pytest
from unittest.mock import MagicMock
from django.utils import timezone
from rest_framework.test import APIRequestFactory
from intercorrencias.models import Intercorrencia, Envolvido, TipoOcorrencia
from intercorrencias.api.serializers.intercorrencia_gipe_serializer import IntercorrenciaGipeSerializer
from intercorrencias.choices.gipe_choices import (
    EnvolveArmaOuAtaque,
    AmeacaFoiRealizadaDeQualManeira,
    CicloAprendizagem,
)
from intercorrencias.choices.info_agressor_choices import MotivoOcorrencia


@pytest.fixture
def request_factory():
    return APIRequestFactory()

@pytest.fixture(autouse=True)
def mock_unidade(monkeypatch):
    """Mock do serviço de unidades para não depender de chamadas externas."""
    def fake_get_unidade(*args, **kwargs):
        return {"codigo_eol": "123", "dre_codigo_eol": "456", "nome": "Unidade Fake"}

    monkeypatch.setattr(
        "intercorrencias.services.unidades_service.get_unidade",
        fake_get_unidade,
    )


@pytest.mark.django_db
class TestIntercorrenciaGipeSerializer:

    @pytest.fixture(autouse=True)
    def setup(self, request_factory):
        self.request = request_factory.post("/fake/")
        self.request.user = MagicMock(
            username="user1",
            unidade_codigo_eol="123",
            dre_codigo_eol="456"
        )

        self.envolvido = Envolvido.objects.create(uuid=uuid.uuid4())
        self.tipo1 = TipoOcorrencia.objects.create(uuid=uuid.uuid4(), nome="Tipo 1")
        self.tipo2 = TipoOcorrencia.objects.create(uuid=uuid.uuid4(), nome="Tipo 2")

        self.intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="diretor",
            unidade_codigo_eol="123",
            dre_codigo_eol="456",
            descricao_ocorrencia="Teste GIPE",
        )

        self.valid_data = {
            "envolve_arma_ataque": EnvolveArmaOuAtaque.SIM,
            "ameaca_realizada_qual_maneira": AmeacaFoiRealizadaDeQualManeira.VIRTUALMENTE,
            "envolvido": str(self.envolvido.uuid),
            "motivacao_ocorrencia": [MotivoOcorrencia.BULLYING],
            "tipos_ocorrencia": [str(self.tipo1.uuid), str(self.tipo2.uuid)],
            "qual_ciclo_aprendizagem": CicloAprendizagem.ALFABETIZACAO,
            "info_sobre_interacoes_virtuais_pessoa_agressora": "Informações",
            "encaminhamentos_gipe": "Encaminhamento X",
            "unidade_codigo_eol": "123",
            "dre_codigo_eol": "456",
            "data_ocorrencia": timezone.now(),
            "user_username": "diretor",
        }

    def test_serializer_valido(self):
        serializer = IntercorrenciaGipeSerializer(
            data=self.valid_data, context={"request": self.request}
        )
        assert serializer.is_valid(), serializer.errors

    def test_tipos_ocorrencia_obrigatorio_quando_lista_vazia(self):
        data = self.valid_data.copy()
        data["tipos_ocorrencia"] = []
        serializer = IntercorrenciaGipeSerializer(
            data=data, context={"request": self.request}
        )
        assert not serializer.is_valid()
        assert "tipos_ocorrencia" in str(serializer.errors)

    def test_motivacao_ocorrencia_deve_ser_lista_nao_vazia(self):
        data = self.valid_data.copy()
        data["motivacao_ocorrencia"] = []
        serializer = IntercorrenciaGipeSerializer(
            data=data, context={"request": self.request}
        )
        assert not serializer.is_valid()
        assert "motivacao_ocorrencia" in str(serializer.errors)

    def test_choice_fields_invalidos(self):
        data = self.valid_data.copy()
        data["envolve_arma_ataque"] = "INVALIDO"
        serializer = IntercorrenciaGipeSerializer(
            data=data, context={"request": self.request}
        )
        assert not serializer.is_valid()
        assert "envolve_arma_ataque" in str(serializer.errors)

    def test_envolvido_invalido(self):
        data = self.valid_data.copy()
        data["envolvido"] = "1234"
        serializer = IntercorrenciaGipeSerializer(
            data=data, context={"request": self.request}
        )
        assert not serializer.is_valid()
        assert "envolvido" in str(serializer.errors)

    def test_tipos_ocorrencia_slug_related_field(self):
        data = self.valid_data.copy()
        data["tipos_ocorrencia"] = ["11111111-1111-1111-1111-111111111111"]
        serializer = IntercorrenciaGipeSerializer(
            data=data, context={"request": self.request}
        )
        assert not serializer.is_valid()
        assert "tipos_ocorrencia" in str(serializer.errors)

    def test_campos_opcionais(self):
        data = self.valid_data.copy()
        data.pop("info_sobre_interacoes_virtuais_pessoa_agressora")

        serializer = IntercorrenciaGipeSerializer(
            data=data, context={"request": self.request}
        )
        assert serializer.is_valid(), serializer.errors

    def test_partial_update(self):
        data = {
            "encaminhamentos_gipe": "Atualizado",
            "unidade_codigo_eol": "123",
            "dre_codigo_eol": "456",
        }
        serializer = IntercorrenciaGipeSerializer(
            instance=self.intercorrencia,
            data=data,
            partial=True,
            context={"request": self.request},
        )
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.encaminhamentos_gipe == "Atualizado"

    def test_get_status_extra(self):
        intercorrencia = self.intercorrencia
        intercorrencia.STATUS_EXTRA_LABELS = {"EM_PREENCHIMENTO": "Em andamento"}
        intercorrencia.status = "EM_PREENCHIMENTO"

        serializer = IntercorrenciaGipeSerializer()
        result = serializer.get_status_extra(intercorrencia)
        assert result == "Em andamento"