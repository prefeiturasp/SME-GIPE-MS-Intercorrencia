import pytest
from uuid import uuid4
from django.utils import timezone
from unittest.mock import patch, MagicMock
from rest_framework import serializers
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError

from intercorrencias.services.unidades_service import ExternalServiceError
from intercorrencias.api.serializers.intercorrencia_serializer import (
    IntercorrenciaSerializer,
    IntercorrenciaDiretorCompletoSerializer,
    IntercorrenciaSecaoInicialSerializer,
    IntercorrenciaFurtoRouboSerializer,
    IntercorrenciaSecaoFinalSerializer,
    IntercorrenciaNaoFurtoRouboSerializer,
    IntercorrenciaInfoAgressorSerializer,
    IntercorrenciaConclusaoDaUeSerializer
)
from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia
from intercorrencias.models.declarante import Declarante
from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia
from intercorrencias.models.envolvido import Envolvido
from intercorrencias.services import unidades_service


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

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_serializer_fields(self, mock_get_unidade):
        mock_get_unidade.return_value = {"nome": "Unidade Teste"}

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
        assert data["nome_unidade"] == "Unidade Teste"
        assert data["nome_dre"] == "Unidade Teste" 

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_get_nome_unidade_quando_servico_lanca_erro(self, mock_get_unidade):
        mock_get_unidade.side_effect = unidades_service.ExternalServiceError("Erro externo")

        intercorrencia = Intercorrencia(
            unidade_codigo_eol="123"
        )
        serializer = IntercorrenciaDiretorCompletoSerializer()

        resultado = serializer.get_nome_unidade(intercorrencia)
        assert resultado is None

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_get_nome_dre_quando_servico_lanca_erro(self, mock_get_unidade):
        mock_get_unidade.side_effect = unidades_service.ExternalServiceError("Erro externo")

        intercorrencia = Intercorrencia(
            dre_codigo_eol="456"
        )
        serializer = IntercorrenciaDiretorCompletoSerializer()

        resultado = serializer.get_nome_dre(intercorrencia)
        assert resultado is None
        
    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_motivacao_ocorrencia_display_diretor_completo(self, mock_get_unidade):
        from intercorrencias.choices.info_agressor_choices import (
            MotivoOcorrencia,
        )
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="user",
            unidade_codigo_eol="123",
            dre_codigo_eol="456",
            sobre_furto_roubo_invasao_depredacao=True,
            motivacao_ocorrencia=["racismo", "bullying"],
        )
        
        serializer = IntercorrenciaDiretorCompletoSerializer()

        display_values = serializer.get_motivacao_ocorrencia_display(intercorrencia)
        
        
        display_values_tratados = [item['label'] for item in display_values]

        expected_displays = [
            MotivoOcorrencia(motivo).label
            for motivo in intercorrencia.motivacao_ocorrencia
        ]
        
        assert display_values_tratados == expected_displays


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
            "envolvido": "Apenas um estudante",
            "tem_info_agressor_ou_vitima": "Não"
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
            "envolvido": "Apenas um estudante",
            "tem_info_agressor_ou_vitima": "Não"
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
            "envolvido": "Apenas um estudante",
            "tem_info_agressor_ou_vitima": "Não" 
        }

        serializer = IntercorrenciaFurtoRouboSerializer(
            instance=intercorrencia, data=data, partial=True
        )

        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)

        assert "Este campo é obrigatório" in str(exc.value)


@pytest.mark.django_db
class TestIntercorrenciaSecaoFinalSerializer:
    """Testes do serializer da seção final (Diretor)"""

    @pytest.fixture
    def declarante_obj(self):
        return Declarante.objects.create(declarante="teste")

    @pytest.fixture
    def intercorrencia_obj(self):
        return Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="diretor1",
            unidade_codigo_eol="123",
            dre_codigo_eol="456",
        )

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_success(self, mock_get, intercorrencia_obj, declarante_obj, auth_request):
        mock_get.return_value = {
            "codigo_eol": "123",
            "dre_codigo_eol": "456"
        }

        data = {
            "declarante": str(declarante_obj.uuid),
            "comunicacao_seguranca_publica": Intercorrencia.SEGURANCA_PUBLICA_CHOICES[0][0],
            "protocolo_acionado": Intercorrencia.PROTOCOLO_CHOICES[0][0],
            "unidade_codigo_eol": "123",
            "dre_codigo_eol": "456",
        }

        serializer = IntercorrenciaSecaoFinalSerializer(
            instance=intercorrencia_obj,
            data=data,
            context={"request": auth_request}
        )

        assert serializer.is_valid(), serializer.errors
        result = serializer.save()
        assert result.declarante == declarante_obj

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_is_valid_error_format_missing_fields(self, mock_get, intercorrencia_obj, auth_request):
        mock_get.return_value = {
            "codigo_eol": "123",
            "dre_codigo_eol": "456"
        }

        data = {
            "declarante": "",
            "comunicacao_seguranca_publica": "",
            "protocolo_acionado": "",
            "unidade_codigo_eol": "123",
            "dre_codigo_eol": "456",
        }

        serializer = IntercorrenciaSecaoFinalSerializer(
            instance=intercorrencia_obj,
            data=data,
            context={"request": auth_request}
        )

        is_valid = serializer.is_valid()
        assert not is_valid
        assert "detail" in serializer.errors

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_is_valid_raise_exception(self, intercorrencia_obj, auth_request):
        data = {
            "declarante": None,
            "comunicacao_seguranca_publica": None,
            "protocolo_acionado": None,
        }
        serializer = IntercorrenciaSecaoFinalSerializer(
            instance=intercorrencia_obj, data=data, context={"request": auth_request}
        )
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "detail" in exc.value.detail

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_is_valid_error_already_has_detail_key(self, mock_get, intercorrencia_obj, declarante_obj, auth_request):
        mock_get.return_value = {
            "codigo_eol": "123",
            "dre_codigo_eol": "999"
        }
        
        data = {
            "declarante": str(declarante_obj.uuid),
            "comunicacao_seguranca_publica": Intercorrencia.SEGURANCA_PUBLICA_CHOICES[0][0],
            "protocolo_acionado": Intercorrencia.PROTOCOLO_CHOICES[0][0],
            "unidade_codigo_eol": "123",
            "dre_codigo_eol": "456",
        }
        
        serializer = IntercorrenciaSecaoFinalSerializer(
            instance=intercorrencia_obj,
            data=data,
            context={"request": auth_request}
        )
        
        is_valid = serializer.is_valid(raise_exception=False)
        
        assert not is_valid
        assert "detail" in serializer.errors
        assert "DRE informada não corresponde" in str(serializer.errors["detail"])


@pytest.mark.django_db
class TestIntercorrenciaNaoFurtoRouboSerializer:
    """Testes do serializer de intercorrências NÃO furto/roubo."""

    def criar_dados_basicos(self, sobre_furto_roubo=False):
        """Cria os objetos necessários para os testes."""
        tipo = TipoOcorrencia.objects.create(nome="Briga entre alunos", ativo=True)
        envolvido = Envolvido.objects.create(perfil_dos_envolvidos="Estudante", ativo=True)

        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            sobre_furto_roubo_invasao_depredacao=sobre_furto_roubo,
            unidade_codigo_eol="U12345",
            dre_codigo_eol="D123",
            user_username="diretor_teste",
        )

        return tipo, envolvido, intercorrencia

    def test_valida_dados_corretos(self):
        tipo, envolvido, intercorrencia = self.criar_dados_basicos(sobre_furto_roubo=False)

        data = {
            "tipos_ocorrencia": [str(tipo.uuid)],
            "descricao_ocorrencia": "Aluno se machucou durante recreio",
            "envolvido": envolvido.uuid,
            "tem_info_agressor_ou_vitima": "nao",
        }

        serializer = IntercorrenciaNaoFurtoRouboSerializer(instance=intercorrencia, data=data)
        assert serializer.is_valid(), serializer.errors

        instancia_salva = serializer.save()
        assert instancia_salva.descricao_ocorrencia == data["descricao_ocorrencia"]

    def test_rejeita_quando_for_furto_roubo(self):
        tipo, envolvido, intercorrencia = self.criar_dados_basicos(sobre_furto_roubo=True)

        data = {
            "tipos_ocorrencia": [str(tipo.uuid)],
            "descricao_ocorrencia": "Roubo de material",
            "envolvido": envolvido.uuid,
            "tem_info_agressor_ou_vitima": "nao",
        }

        serializer = IntercorrenciaNaoFurtoRouboSerializer(instance=intercorrencia, data=data)
        assert not serializer.is_valid()
        assert "furto/roubo" in str(serializer.errors).lower()

    def test_rejeita_quando_tipos_ocorrencia_vazio(self):
        _, envolvido, intercorrencia = self.criar_dados_basicos(sobre_furto_roubo=False)

        data = {
            "tipos_ocorrencia": [],
            "descricao_ocorrencia": "Ocorrência sem tipo",
            "envolvido": envolvido.uuid,
            "tem_info_agressor_ou_vitima": "sim",
        }

        serializer = IntercorrenciaNaoFurtoRouboSerializer(instance=intercorrencia, data=data)
        assert not serializer.is_valid()
        assert "tipos_ocorrencia" in serializer.errors["detail"]

    def test_rejeita_quando_envolvido_invalido(self):
        tipo, _, intercorrencia = self.criar_dados_basicos(sobre_furto_roubo=False)

        data = {
            "tipos_ocorrencia": [str(tipo.uuid)],
            "descricao_ocorrencia": "Teste com envolvido inválido",
            "envolvido": 9999,
            "tem_info_agressor_ou_vitima": "sim",
        }

        serializer = IntercorrenciaNaoFurtoRouboSerializer(instance=intercorrencia, data=data)
        assert not serializer.is_valid()
        assert "envolvido" in serializer.errors.get("detail", "")

    def test_is_valid_raise_exception_quando_invalido(self):
        serializer = IntercorrenciaNaoFurtoRouboSerializer(
            instance=Intercorrencia(sobre_furto_roubo_invasao_depredacao=False),
            data={} 
        )

        with pytest.raises(serializers.ValidationError) as exc:
            serializer.is_valid(raise_exception=True)

        assert "detail" in exc.value.detail


@pytest.mark.django_db
class TestIntercorrenciaInfoAgressorSerializer:

    @pytest.fixture(autouse=True)
    def setup_method(self, request_factory):
        self.request = request_factory.post("/fake-url/")
        self.request.user = MagicMock(unidade_codigo_eol="123456")
        self.intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="diretor1",
            unidade_codigo_eol="123456",
            dre_codigo_eol="654321",
            tem_info_agressor_ou_vitima="sim",
            motivacao_ocorrencia=["racismo", "bullying"],
        )
        self.valid_data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "nome_pessoa_agressora": "João Silva",
            "idade_pessoa_agressora": 17,
            "motivacao_ocorrencia": ["racismo", "bullying"],
            "genero_pessoa_agressora": "homem_cis",
            "grupo_etnico_racial": "preto",
            "etapa_escolar": "ensino_medio",
            "frequencia_escolar": "regularizada",
            "interacao_ambiente_escolar": "Interage bem com os colegas.",
            "redes_protecao_acompanhamento": "CREAS",
            "notificado_conselho_tutelar": True,
            "acompanhado_naapa": False,
            "cep": "01001-000",
            "logradouro": "Rua das Flores",
            "numero_residencia": "123",
            "complemento": "",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "estado": "São Paulo",
        }

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_serializer_valido(self, mock_get_unidade):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        serializer = IntercorrenciaInfoAgressorSerializer(
            instance=self.intercorrencia, data=self.valid_data, context={"request": self.request}
        )
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.nome_pessoa_agressora == "João Silva"

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_serializer_invalido_quando_tem_info_false(self, mock_get_unidade):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="diretor2",
            unidade_codigo_eol="123456",
            dre_codigo_eol="654321",
            tem_info_agressor_ou_vitima="nao",
        )
        serializer = IntercorrenciaInfoAgressorSerializer(
            instance=intercorrencia, data=self.valid_data, context={"request": self.request}
        )
        assert not serializer.is_valid()
        assert "detail" in serializer.errors
        error_message = str(serializer.errors["detail"])
        assert "Não é possível preencher informações de agressor/vítima" in error_message

    @pytest.mark.parametrize(
        "campo",
        [
            "nome_pessoa_agressora",
            "motivacao_ocorrencia",
            "cep",
            "logradouro",
            "bairro",
            "cidade",
            "estado",
        ],
    )
    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_campo_obrigatorio_nao_informado(self, mock_get_unidade, campo):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        data = self.valid_data.copy()
        data.pop(campo)
        serializer = IntercorrenciaInfoAgressorSerializer(
            instance=self.intercorrencia, data=data, context={"request": self.request}
        )
        assert not serializer.is_valid()
        assert "detail" in serializer.errors
        assert campo in serializer.errors["detail"]
        
    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_campo_motivacao_ocorrencia_vazio(self, mock_get_unidade):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        data = self.valid_data.copy()
        data["motivacao_ocorrencia"] = []
        serializer = IntercorrenciaInfoAgressorSerializer(
            instance=self.intercorrencia, data=data, context={"request": self.request}
        )
        assert not serializer.is_valid()
        assert "detail" in serializer.errors
        assert "motivacao_ocorrencia" in serializer.errors["detail"]
        assert "Esta lista não pode estar vazia." in serializer.errors["detail"]
        
    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_campo_motivacao_ocorrencia_errado(self, mock_get_unidade):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        data = self.valid_data.copy()
        data["motivacao_ocorrencia"] = ["motivo_invalido"]
        serializer = IntercorrenciaInfoAgressorSerializer(
            instance=self.intercorrencia, data=data, context={"request": self.request}
        )
        assert not serializer.is_valid()
        assert "detail" in serializer.errors
        assert "motivacao_ocorrencia" in serializer.errors["detail"]
        assert '"motivo_invalido" não é um escolha válida.' in str(serializer.errors["detail"])
        
    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_motivacao_ocorrencia_display(self, mock_get_unidade):
        from intercorrencias.choices.info_agressor_choices import (
            MotivoOcorrencia,
        )
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        serializer = IntercorrenciaInfoAgressorSerializer(
            instance=self.intercorrencia, data=self.valid_data, context={"request": self.request}
        )
        assert serializer.is_valid(), serializer.errors
        display_values = serializer.get_motivacao_ocorrencia_display(self.intercorrencia)
        
        
        display_values_tratados = [item['label'] for item in display_values]

        expected_displays = [
            MotivoOcorrencia(motivo).label
            for motivo in self.valid_data["motivacao_ocorrencia"]
        ]
        
        assert display_values_tratados == expected_displays
        
        
    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_motivacao_ocorrencia_display_vazio(self, mock_get_unidade):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="diretor3",
            unidade_codigo_eol="123456",
            dre_codigo_eol="654321",
            tem_info_agressor_ou_vitima="sim",
            motivacao_ocorrencia=[],
        )
        serializer = IntercorrenciaInfoAgressorSerializer(
            instance=intercorrencia, data=self.valid_data, context={"request": self.request}
        )
        assert serializer.is_valid(), serializer.errors
        display_values = serializer.get_motivacao_ocorrencia_display(intercorrencia)
        
        assert display_values == []
        
    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_motivacao_ocorrencia_none(self, mock_get_unidade):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        data = self.valid_data.copy()
        data["motivacao_ocorrencia"] = None
        serializer = IntercorrenciaInfoAgressorSerializer(
            instance=self.intercorrencia, data=data, context={"request": self.request}
        )
        assert not serializer.is_valid()
        assert "detail" in serializer.errors
        assert "motivacao_ocorrencia" in serializer.errors["detail"]
        assert "Este campo não pode ser nulo." in serializer.errors["detail"]

    def test_validate_motivacao_ocorrencia_vazio_direto(self):
        """Testa validate_motivacao_ocorrencia diretamente com lista vazia"""
        serializer = IntercorrenciaInfoAgressorSerializer()
        
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_motivacao_ocorrencia([])
        
        assert "Selecione pelo menos uma motivação." in str(exc_info.value)

    def test_validate_motivacao_ocorrencia_none_direto(self):
        """Testa validate_motivacao_ocorrencia diretamente com None"""
        serializer = IntercorrenciaInfoAgressorSerializer()
        
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_motivacao_ocorrencia(None)
        
        assert "Selecione pelo menos uma motivação." in str(exc_info.value)

    def test_validate_motivacao_ocorrencia_valor_invalido_direto(self):
        """Testa validate_motivacao_ocorrencia diretamente com valor inválido"""
        serializer = IntercorrenciaInfoAgressorSerializer()
        
        with pytest.raises(serializers.ValidationError) as exc_info:
            serializer.validate_motivacao_ocorrencia(["motivo_inexistente"])
        
        assert "'motivo_inexistente' não é uma motivação válida." in str(exc_info.value)

    def test_validate_motivacao_ocorrencia_remove_duplicatas(self):
        """Testa que validate_motivacao_ocorrencia remove duplicatas"""
        serializer = IntercorrenciaInfoAgressorSerializer()
        
        # Lista com duplicatas
        result = serializer.validate_motivacao_ocorrencia(["racismo", "bullying", "racismo", "bullying"])
        
        # Deve remover duplicatas
        assert len(result) == 2
        assert "racismo" in result
        assert "bullying" in result

    @pytest.mark.parametrize(
        "campo",
        [
            "nome_pessoa_agressora",
            "interacao_ambiente_escolar",
            "logradouro",
            "bairro",
            "cidade",
        ],
    )
    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_campo_nao_pode_ser_branco(self, mock_get_unidade, campo):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        data = self.valid_data.copy()
        data[campo] = ""
        serializer = IntercorrenciaInfoAgressorSerializer(
            instance=self.intercorrencia, data=data, context={"request": self.request}
        )
        assert not serializer.is_valid()
        assert "detail" in serializer.errors
        assert campo in serializer.errors["detail"]
        assert "não pode estar em branco" in serializer.errors["detail"]

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_campo_complemento_pode_ser_vazio(self, mock_get_unidade):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        data = self.valid_data.copy()
        data["complemento"] = ""
        serializer = IntercorrenciaInfoAgressorSerializer(
            instance=self.intercorrencia, data=data, context={"request": self.request}
        )
        assert serializer.is_valid(), serializer.errors

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_serializer_erro_formato_detail(self, mock_get_unidade):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="diretor3",
            unidade_codigo_eol="123456",
            dre_codigo_eol="654321",
            tem_info_agressor_ou_vitima="nao",
        )
        serializer = IntercorrenciaInfoAgressorSerializer(
            instance=intercorrencia, data=self.valid_data, context={"request": self.request}
        )
        assert not serializer.is_valid()
        assert "detail" in serializer.errors
        
        
@pytest.mark.django_db
class TestIntercorrenciaConclusaoDaUeSerializer:
    """Testes do serializer de conclusão da intercorrência (Diretor)"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self, request_factory):
        self.request = request_factory.post("/fake-url/")
        self.request.user = MagicMock(unidade_codigo_eol="123456")
        self.intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="diretor1",
            unidade_codigo_eol="123456",
            dre_codigo_eol="654321",
        )
        self.valid_data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "motivo_encerramento_ue": "Este é o motivo do encerramento da UE"
        }
        
    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_serializer_conclusao_ue_valido(self, mock_get_unidade):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia, data=self.valid_data, context={"request": self.request}
        )
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.motivo_encerramento_ue == "Este é o motivo do encerramento da UE"


    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_validate_dre_incorreta(self, mock_get, intercorrencia_data, request):
        mock_get.return_value = {"codigo_eol": "123", "dre_codigo_eol": "999"}

        serializer = IntercorrenciaConclusaoDaUeSerializer(
            data=intercorrencia_data, context={"request": request}
        )
        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=True)   
            
    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_campo_obrigatorio_nao_informado(self, mock_get_unidade):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        data = self.valid_data.copy()
        data.pop("motivo_encerramento_ue")
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia, data=data, context={"request": self.request}
        )
        assert not serializer.is_valid()
        assert "detail" in serializer.errors
        assert "motivo_encerramento_ue" in serializer.errors["detail"]
        
    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_get_nome_unidade_quando_servico_lanca_erro(self, mock_get_unidade):
        mock_get_unidade.side_effect = unidades_service.ExternalServiceError("Erro externo")

        intercorrencia = Intercorrencia(
            unidade_codigo_eol="123"
        )
        serializer = IntercorrenciaConclusaoDaUeSerializer()

        resultado = serializer.get_nome_unidade(intercorrencia)
        assert resultado is None

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_get_nome_dre_quando_servico_lanca_erro(self, mock_get_unidade):
        mock_get_unidade.side_effect = unidades_service.ExternalServiceError("Erro externo")

        intercorrencia = Intercorrencia(
            dre_codigo_eol="456"
        )
        serializer = IntercorrenciaConclusaoDaUeSerializer()

        resultado = serializer.get_nome_dre(intercorrencia)
        assert resultado is None

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_responsavel_nome_com_usuario_valido(self, mock_get_unidade):
        """Testa get_responsavel_nome quando usuário tem o atributo 'name'"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        # Configura o mock do usuário com o atributo 'name'
        self.request.user.name = "João da Silva"
        self.request.user.unidade_codigo_eol = "123456"
        
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia, 
            context={"request": self.request}
        )
        
        resultado = serializer.get_responsavel_nome(self.intercorrencia)
        assert resultado == "João da Silva"

    def test_get_responsavel_nome_sem_request_no_context(self):
        """Testa get_responsavel_nome quando não há request no context"""
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={}
        )
        
        resultado = serializer.get_responsavel_nome(self.intercorrencia)
        assert resultado is None

    def test_get_responsavel_nome_request_sem_user(self):
        """Testa get_responsavel_nome quando request não tem user"""
        request_sem_user = MagicMock()
        delattr(request_sem_user, 'user')
        
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={"request": request_sem_user}
        )
        
        resultado = serializer.get_responsavel_nome(self.intercorrencia)
        assert resultado is None

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_responsavel_nome_user_sem_atributo_name(self, mock_get_unidade):
        """Testa get_responsavel_nome quando user não tem atributo 'name'"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        # Configura o mock do usuário SEM o atributo 'name'
        self.request.user = MagicMock(unidade_codigo_eol="123456")
        # Remove explicitamente o atributo 'name'
        self.request.user.name = None
        
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )
        
        resultado = serializer.get_responsavel_nome(self.intercorrencia)
        assert resultado is None

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_responsavel_cpf_com_cpf_valido(self, mock_get_unidade):
        """Testa get_responsavel_cpf com CPF válido de 11 dígitos"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        self.request.user = MagicMock(
            unidade_codigo_eol="123456",
            cpf="12345678901"
        )
        
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )
        
        resultado = serializer.get_responsavel_cpf(self.intercorrencia)
        assert resultado == "123.456.789-01"

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_responsavel_cpf_invalido(self, mock_get_unidade):
        """Testa get_responsavel_cpf com CPF inválido (não numérico ou tamanho incorreto)"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        self.request.user = MagicMock(
            unidade_codigo_eol="123456",
            cpf="123.456.789-01"  # CPF já formatado (não numérico)
        )
        
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )
        
        resultado = serializer.get_responsavel_cpf(self.intercorrencia)
        assert resultado == "123.456.789-01"  # Retorna sem formatar

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_responsavel_cpf_sem_cpf(self, mock_get_unidade):
        """Testa get_responsavel_cpf quando user não tem CPF"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        self.request.user = MagicMock(unidade_codigo_eol="123456")
        self.request.user.cpf = None
        
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )
        
        resultado = serializer.get_responsavel_cpf(self.intercorrencia)
        assert resultado is None
        
    def test_get_responsavel_cpf_sem_request_no_context(self):
        """Testa get_responsavel_cpf quando não há request no context"""
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={}
        )
        
        resultado = serializer.get_responsavel_cpf(self.intercorrencia)
        assert resultado is None
        

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_responsavel_email_com_email_valido(self, mock_get_unidade):
        """Testa get_responsavel_email com email válido"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        self.request.user = MagicMock(
            unidade_codigo_eol="123456",
            email="joao.silva@sme.prefeitura.sp.gov.br"
        )
        
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )
        
        resultado = serializer.get_responsavel_email(self.intercorrencia)
        assert resultado == "joao.silva@sme.prefeitura.sp.gov.br"

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_responsavel_email_sem_email(self, mock_get_unidade):
        """Testa get_responsavel_email quando user não tem email"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        self.request.user = MagicMock(unidade_codigo_eol="123456")
        self.request.user.email = None
        
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )
        
        resultado = serializer.get_responsavel_email(self.intercorrencia)
        assert resultado is None
        
    def test_get_responsavel_email_sem_request_no_context(self):
        """Testa get_responsavel_email quando não há request no context"""
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={}
        )
        
        resultado = serializer.get_responsavel_email(self.intercorrencia)
        assert resultado is None

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_perfil_acesso_diretor(self, mock_get_unidade):
        """Testa get_perfil_acesso para perfil Diretor"""
        from config.settings import CODIGO_PERFIL_DIRETOR
        
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        self.request.user = MagicMock(
            unidade_codigo_eol="123456",
            cargo_codigo=CODIGO_PERFIL_DIRETOR
        )
        
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )
        
        resultado = serializer.get_perfil_acesso(self.intercorrencia)
        assert resultado == "Diretor(a) Pedagógico"

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_perfil_acesso_assistente_direcao(self, mock_get_unidade):
        """Testa get_perfil_acesso para perfil Assistente de Direção"""
        from config.settings import CODIGO_PERFIL_ASSISTENTE_DIRECAO
        
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        self.request.user = MagicMock(
            unidade_codigo_eol="123456",
            cargo_codigo=CODIGO_PERFIL_ASSISTENTE_DIRECAO
        )
        
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )
        
        resultado = serializer.get_perfil_acesso(self.intercorrencia)
        assert resultado == "Assistente de Direção"

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_perfil_acesso_dre(self, mock_get_unidade):
        """Testa get_perfil_acesso para perfil DRE"""
        from config.settings import CODIGO_PERFIL_DRE
        
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        self.request.user = MagicMock(
            unidade_codigo_eol="123456",
            cargo_codigo=CODIGO_PERFIL_DRE
        )
        
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )
        
        resultado = serializer.get_perfil_acesso(self.intercorrencia)
        assert resultado == "Ponto Focal DRE"

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_perfil_acesso_codigo_nao_definido(self, mock_get_unidade):
        """Testa get_perfil_acesso para código de perfil não mapeado"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        self.request.user = MagicMock(
            unidade_codigo_eol="123456",
            cargo_codigo=99999  # Código não mapeado
        )
        
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )
        
        resultado = serializer.get_perfil_acesso(self.intercorrencia)
        assert resultado == "Não definido"

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_get_perfil_acesso_sem_cargo_codigo(self, mock_get_unidade):
        """Testa get_perfil_acesso quando user não tem cargo_codigo"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        self.request.user = MagicMock(unidade_codigo_eol="123456")
        self.request.user.cargo_codigo = None
        
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )
        
        resultado = serializer.get_perfil_acesso(self.intercorrencia)
        assert resultado == "Não definido"
        
        
    def test_get_perfil_acesso_sem_request_no_context(self):
        """Testa get_perfil_acesso quando não há request no context"""
        serializer = IntercorrenciaConclusaoDaUeSerializer(
            instance=self.intercorrencia,
            context={}
        )
        
        resultado = serializer.get_perfil_acesso(self.intercorrencia)
        assert resultado is None
        
        
@pytest.mark.django_db
class TestIntercorrenciaUpdateDiretorCompletoSerializer:
    """Testes do serializer de atualização completa"""

    @pytest.fixture(autouse=True)
    def setup_method(self, request_factory):
        self.request = request_factory.post("/fake-url/")
        self.request.user = MagicMock(unidade_codigo_eol="123456")
        
        # Cria uma intercorrência com informações de agressor preenchidas
        self.intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="diretor1",
            unidade_codigo_eol="123456",
            dre_codigo_eol="654321",
            sobre_furto_roubo_invasao_depredacao=False,
            tem_info_agressor_ou_vitima="sim",
            nome_pessoa_agressora="João da Silva",
            idade_pessoa_agressora=17,
            motivacao_ocorrencia=["racismo", "bullying"],
            genero_pessoa_agressora="homem_cis",
            grupo_etnico_racial="preto",
            etapa_escolar="ensino_medio",
            frequencia_escolar="regularizada",
            interacao_ambiente_escolar="Interage bem com os colegas",
            redes_protecao_acompanhamento="CREAS",
            notificado_conselho_tutelar=True,
            acompanhado_naapa=False,
            cep="01001-000",
            logradouro="Rua das Flores",
            numero_residencia="123",
            complemento="Apto 45",
            bairro="Centro",
            cidade="São Paulo",
            estado="São Paulo",
        )

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_limpa_campos_agressor_quando_tem_info_muda_para_nao(self, mock_get_unidade):
        """Testa que campos de agressor são limpos quando tem_info_agressor_ou_vitima muda para 'nao'"""
        from intercorrencias.api.serializers.intercorrencia_serializer import (
            IntercorrenciaUpdateDiretorCompletoSerializer,
        )
        
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        # Verifica que os campos estão preenchidos antes
        assert self.intercorrencia.nome_pessoa_agressora == "João da Silva"
        assert self.intercorrencia.idade_pessoa_agressora == 17
        assert self.intercorrencia.motivacao_ocorrencia == ["racismo", "bullying"]
        assert self.intercorrencia.cep == "01001-000"
        
        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "tem_info_agressor_ou_vitima": "nao",
        }
        
        serializer = IntercorrenciaUpdateDiretorCompletoSerializer(
            instance=self.intercorrencia,
            data=data,
            partial=True,
            context={"request": self.request}
        )
        
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        
        # Recarrega da base de dados
        instance.refresh_from_db()
        
        # Verifica que todos os campos foram limpos
        assert instance.nome_pessoa_agressora == ""
        assert instance.idade_pessoa_agressora is None
        assert instance.motivacao_ocorrencia == []
        assert instance.genero_pessoa_agressora == ""
        assert instance.grupo_etnico_racial == ""
        assert instance.etapa_escolar == ""
        assert instance.frequencia_escolar == ""
        assert instance.interacao_ambiente_escolar == ""
        assert instance.redes_protecao_acompanhamento == ""
        assert instance.notificado_conselho_tutelar is None
        assert instance.acompanhado_naapa is None
        assert instance.cep == ""
        assert instance.logradouro == ""
        assert instance.numero_residencia == ""
        assert instance.complemento == ""
        assert instance.bairro == ""
        assert instance.cidade == ""
        assert instance.estado == ""

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_mantem_campos_agressor_quando_tem_info_permanece_sim(self, mock_get_unidade):
        """Testa que campos de agressor são mantidos quando tem_info_agressor_ou_vitima permanece 'sim'"""
        from intercorrencias.api.serializers.intercorrencia_serializer import (
            IntercorrenciaUpdateDiretorCompletoSerializer,
        )
        
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "tem_info_agressor_ou_vitima": "sim",
            "descricao_ocorrencia": "Atualização da descrição",
        }
        
        serializer = IntercorrenciaUpdateDiretorCompletoSerializer(
            instance=self.intercorrencia,
            data=data,
            partial=True,
            context={"request": self.request}
        )
        
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        
        # Recarrega da base de dados
        instance.refresh_from_db()
        
        # Verifica que os campos NÃO foram limpos
        assert instance.nome_pessoa_agressora == "João da Silva"
        assert instance.idade_pessoa_agressora == 17
        assert instance.motivacao_ocorrencia == ["racismo", "bullying"]
        assert instance.cep == "01001-000"
        assert instance.descricao_ocorrencia == "Atualização da descrição"

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_limpa_smart_sampa_quando_nao_e_furto_roubo(self, mock_get_unidade):
        """Testa que smart_sampa_situacao é limpo quando NÃO é furto/roubo"""
        from intercorrencias.api.serializers.intercorrencia_serializer import (
            IntercorrenciaUpdateDiretorCompletoSerializer,
        )
        
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        # Cria uma intercorrência que NÃO é furto/roubo mas tem smart_sampa preenchido
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="diretor1",
            unidade_codigo_eol="123456",
            dre_codigo_eol="654321",
            sobre_furto_roubo_invasao_depredacao=False,
            smart_sampa_situacao="sim_com_dano",
        )
        
        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "descricao_ocorrencia": "Teste",
        }
        
        serializer = IntercorrenciaUpdateDiretorCompletoSerializer(
            instance=intercorrencia,
            data=data,
            partial=True,
            context={"request": self.request}
        )
        
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        
        # Recarrega da base de dados
        instance.refresh_from_db()
        
        # Verifica que smart_sampa_situacao foi limpo
        assert instance.smart_sampa_situacao == ""

    @patch("intercorrencias.services.unidades_service.get_unidade")
    def test_limpa_envolvido_quando_e_furto_roubo(self, mock_get_unidade):
        """Testa que envolvido e tem_info_agressor_ou_vitima são limpos quando É furto/roubo"""
        from intercorrencias.api.serializers.intercorrencia_serializer import (
            IntercorrenciaUpdateDiretorCompletoSerializer,
        )
        from intercorrencias.models.envolvido import Envolvido
        
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        # Cria um envolvido
        envolvido = Envolvido.objects.create(perfil_dos_envolvidos="Estudante", ativo=True)
        
        # Cria uma intercorrência que É furto/roubo mas tem envolvido
        intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="diretor1",
            unidade_codigo_eol="123456",
            dre_codigo_eol="654321",
            sobre_furto_roubo_invasao_depredacao=True,
            envolvido=envolvido,
            tem_info_agressor_ou_vitima="sim",
        )
        
        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "descricao_ocorrencia": "Teste furto",
        }
        
        serializer = IntercorrenciaUpdateDiretorCompletoSerializer(
            instance=intercorrencia,
            data=data,
            partial=True,
            context={"request": self.request}
        )
        
        assert serializer.is_valid(), serializer.errors
        instance = serializer.save()
        
        # Recarrega da base de dados
        instance.refresh_from_db()
        
        # Verifica que envolvido e tem_info_agressor_ou_vitima foram limpos
        assert instance.envolvido is None
        assert instance.tem_info_agressor_ou_vitima == ""
                