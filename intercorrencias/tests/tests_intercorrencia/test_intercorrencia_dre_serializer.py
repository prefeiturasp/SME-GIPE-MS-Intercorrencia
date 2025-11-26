import pytest
from django.utils import timezone
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory

from intercorrencias.services import unidades_service
from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.api.serializers.intercorrencia_dre_serializer import (
    IntercorrenciaDreSerializer,
    IntercorrenciaConclusaoDaDreSerializer
)


@pytest.fixture
def request_factory_dre():
    return APIRequestFactory()


@pytest.mark.django_db
class TestIntercorrenciaDreSerializer:
    """Testes do serializer de intercorrência para DRE"""
    
    @pytest.fixture(autouse=True)
    def setup_method(self, request_factory_dre):
        self.request = request_factory_dre.post("/fake-url/")
        self.request.user = MagicMock(unidade_codigo_eol="654321", dre_codigo_eol="654321")
        self.intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="diretor1",
            unidade_codigo_eol="123456",
            dre_codigo_eol="654321",
            descricao_ocorrencia="Descrição inicial",
        )
        self.valid_data = {
            "unidade_codigo_eol": '123456',
            "dre_codigo_eol": '654321',
            "acionamento_seguranca_publica": True,
            "interlocucao_sts": True,
            "info_complementar_sts": "Info STS",
        }
        
    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_serializer_dre_valido(self, mock_get_unidade):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        serializer = IntercorrenciaDreSerializer(
            instance=self.intercorrencia, 
            data=self.valid_data, 
            context={"request": self.request},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.acionamento_seguranca_publica == True
        assert obj.interlocucao_sts == True
        
    
    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_dre_nao_pode_atualizar_unidade_de_outra_dre(self, mock_get_unidade):
        """DRE não deve conseguir atualizar intercorrências de unidades de outra DRE"""
        # Mock retorna unidade de DRE diferente
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "999999"}
        serializer = IntercorrenciaDreSerializer(
            instance=self.intercorrencia,
            data=self.valid_data,
            context={"request": self.request},
            partial=True
        )
        assert not serializer.is_valid()
        assert "detail" in serializer.errors
        assert "DRE informada não corresponde à DRE da unidade." in str(serializer.errors["detail"])
    

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_campos_booleanos_obrigatorios(self, mock_get_unidade):
        """Testa que campos booleanos funcionam corretamente quando enviados"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        # Com partial=True, campos não enviados não são obrigatórios
        # Este teste verifica que quando são enviados, funcionam corretamente
        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "acionamento_seguranca_publica": True,
            "interlocucao_sts": False,
            "interlocucao_cpca": False,
            "interlocucao_supervisao_escolar": False,
            "interlocucao_naapa": False,
        }
        serializer = IntercorrenciaDreSerializer(
            instance=self.intercorrencia,
            data=data,
            context={"request": self.request},
            partial=True
        )
        
        # Deve ser válido com todos os booleanos preenchidos
        assert serializer.is_valid(), serializer.errors


    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_validacao_completa_com_todos_campos_preenchidos(self, mock_get_unidade):
        """Valida cenário completo com todos os campos preenchidos corretamente"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        
        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "acionamento_seguranca_publica": True,
            "interlocucao_sts": True,
            "info_complementar_sts": "Informação sobre STS",
            "interlocucao_cpca": True,
            "info_complementar_cpca": "Informação sobre CPCA",
            "interlocucao_supervisao_escolar": True,
            "info_complementar_supervisao_escolar": "Informação sobre Supervisão",
            "interlocucao_naapa": True,
            "info_complementar_naapa": "Informação sobre NAAPA",
        }
        serializer = IntercorrenciaDreSerializer(
            instance=self.intercorrencia,
            data=data,
            context={"request": self.request},
            partial=True
        )
        
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.interlocucao_sts is True
        assert obj.info_complementar_sts == "Informação sobre STS"
        assert obj.interlocucao_cpca is True
        assert obj.info_complementar_cpca == "Informação sobre CPCA"

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_info_complementar_sts_obrigatorio_quando_interlocucao_true(self, mock_get_unidade):
        """info_complementar_sts deve ser obrigatorio quando interlocucao_sts e True"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "acionamento_seguranca_publica": True,
            "interlocucao_sts": True,
            "info_complementar_sts": "",
            "interlocucao_cpca": False,
            "interlocucao_supervisao_escolar": False,
            "interlocucao_naapa": False,
        }
        serializer = IntercorrenciaDreSerializer(
            instance=self.intercorrencia,
            data=data,
            context={"request": self.request},
            partial=True
        )
        assert not serializer.is_valid()
        assert "info_complementar_sts" in str(serializer.errors)

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_info_complementar_cpca_obrigatorio_quando_interlocucao_true(self, mock_get_unidade):
        """info_complementar_cpca deve ser obrigatorio quando interlocucao_cpca e True"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "acionamento_seguranca_publica": False,
            "interlocucao_sts": False,
            "interlocucao_cpca": True,
            "info_complementar_cpca": "",
            "interlocucao_supervisao_escolar": False,
            "interlocucao_naapa": False,
        }
        serializer = IntercorrenciaDreSerializer(
            instance=self.intercorrencia,
            data=data,
            context={"request": self.request},
            partial=True
        )
        assert not serializer.is_valid()
        assert "info_complementar_cpca" in str(serializer.errors)

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_info_complementar_supervisao_obrigatorio_quando_interlocucao_true(self, mock_get_unidade):
        """info_complementar_supervisao_escolar deve ser obrigatorio quando interlocucao_supervisao_escolar e True"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "acionamento_seguranca_publica": False,
            "interlocucao_sts": False,
            "interlocucao_cpca": False,
            "interlocucao_supervisao_escolar": True,
            "info_complementar_supervisao_escolar": "",
            "interlocucao_naapa": False,
        }
        serializer = IntercorrenciaDreSerializer(
            instance=self.intercorrencia,
            data=data,
            context={"request": self.request},
            partial=True
        )
        assert not serializer.is_valid()
        assert "info_complementar_supervisao_escolar" in str(serializer.errors)

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_info_complementar_naapa_obrigatorio_quando_interlocucao_true(self, mock_get_unidade):
        """info_complementar_naapa deve ser obrigatorio quando interlocucao_naapa e True"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "acionamento_seguranca_publica": False,
            "interlocucao_sts": False,
            "interlocucao_cpca": False,
            "interlocucao_supervisao_escolar": False,
            "interlocucao_naapa": True,
            "info_complementar_naapa": "",
        }
        serializer = IntercorrenciaDreSerializer(
            instance=self.intercorrencia,
            data=data,
            context={"request": self.request},
            partial=True
        )
        assert not serializer.is_valid()
        assert "info_complementar_naapa" in str(serializer.errors)

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_info_complementar_nao_obrigatorio_quando_interlocucao_false(self, mock_get_unidade):
        """info_complementar nao deve ser obrigatorio quando interlocucao e False"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "acionamento_seguranca_publica": True,
            "interlocucao_sts": False,
            "info_complementar_sts": "",
            "interlocucao_cpca": False,
            "info_complementar_cpca": "",
            "interlocucao_supervisao_escolar": False,
            "info_complementar_supervisao_escolar": "",
            "interlocucao_naapa": False,
            "info_complementar_naapa": "",
        }
        serializer = IntercorrenciaDreSerializer(
            instance=self.intercorrencia,
            data=data,
            context={"request": self.request},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors

    @patch("intercorrencias.api.serializers.intercorrencia_serializer.unidades_service.get_unidade")
    def test_validacao_completa_todos_campos_preenchidos(self, mock_get_unidade):
        """Valida cenario completo com todos os campos preenchidos corretamente"""
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}
        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "acionamento_seguranca_publica": True,
            "interlocucao_sts": True,
            "info_complementar_sts": "Informacao sobre STS",
            "interlocucao_cpca": True,
            "info_complementar_cpca": "Informacao sobre CPCA",
            "interlocucao_supervisao_escolar": True,
            "info_complementar_supervisao_escolar": "Informacao sobre Supervisao",
            "interlocucao_naapa": True,
            "info_complementar_naapa": "Informacao sobre NAAPA",
        }
        serializer = IntercorrenciaDreSerializer(
            instance=self.intercorrencia,
            data=data,
            context={"request": self.request},
            partial=True
        )
        assert serializer.is_valid(), serializer.errors
        obj = serializer.save()
        assert obj.interlocucao_sts is True
        assert obj.info_complementar_sts == "Informacao sobre STS"


    def test_get_status_extra_method_returns_expected_label(self):
        intercorrencia = MagicMock(status="EM_PREENCHIMENTO")
        intercorrencia.STATUS_EXTRA_LABELS = {"EM_PREENCHIMENTO": "Em andamento"}
        serializer = IntercorrenciaDreSerializer()
        result = serializer.get_status_extra(intercorrencia)
        assert result == "Em andamento"


@pytest.mark.django_db
class TestIntercorrenciaConclusaoDaDreSerializer:

    @pytest.fixture(autouse=True)
    def setup(self, request_factory_dre):
        self.request = request_factory_dre.post("/fake-url/")

        self.request.user = MagicMock()
        self.request.user.name = "João da Silva"
        self.request.user.cpf = "12345678901"
        self.request.user.email = "joao.silva@teste.com"

        self.intercorrencia = Intercorrencia.objects.create(
            data_ocorrencia=timezone.now(),
            user_username="diretor1",
            unidade_codigo_eol="123456",
            dre_codigo_eol="654321",
            descricao_ocorrencia="Descrição inicial",
            motivo_encerramento_dre="Encerrado por teste",
        )

    @patch("intercorrencias.api.serializers.intercorrencia_dre_serializer.unidades_service.get_unidade")
    def test_get_nome_dre_sucesso(self, mock_get_unidade):
        mock_get_unidade.return_value = {"nome": "DRE Norte"}

        serializer = IntercorrenciaConclusaoDaDreSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )

        assert serializer.data["nome_dre"] == "DRE Norte"

    @patch("intercorrencias.api.serializers.intercorrencia_dre_serializer.unidades_service.get_unidade")
    def test_get_nome_dre_quando_servico_falha(self, mock_get_unidade):
        mock_get_unidade.side_effect = unidades_service.ExternalServiceError()

        serializer = IntercorrenciaConclusaoDaDreSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )

        assert serializer.data["nome_dre"] is None

    def test_get_responsavel_nome(self):
        serializer = IntercorrenciaConclusaoDaDreSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )

        assert serializer.data["responsavel_nome"] == "João da Silva"

    def test_get_responsavel_email(self):
        serializer = IntercorrenciaConclusaoDaDreSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )

        assert serializer.data["responsavel_email"] == "joao.silva@teste.com"

    def test_get_responsavel_cpf_com_formatacao(self):
        serializer = IntercorrenciaConclusaoDaDreSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )

        assert serializer.data["responsavel_cpf"] == "123.456.789-01"

    def test_get_responsavel_cpf_invalido(self):
        self.request.user.cpf = "ABC123"

        serializer = IntercorrenciaConclusaoDaDreSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )

        assert serializer.data["responsavel_cpf"] == "ABC123"

    def test_get_responsavel_cpf_none(self):
        self.request.user.cpf = None

        serializer = IntercorrenciaConclusaoDaDreSerializer(
            instance=self.intercorrencia,
            context={"request": self.request}
        )

        assert serializer.data["responsavel_cpf"] is None

    def test_metodos_sem_request_no_contexto(self):
        serializer = IntercorrenciaConclusaoDaDreSerializer(
            instance=self.intercorrencia,
            context={}
        )

        assert serializer.get_responsavel_nome(self.intercorrencia) is None
        assert serializer.get_responsavel_cpf(self.intercorrencia) is None
        assert serializer.get_responsavel_email(self.intercorrencia) is None

    @patch("intercorrencias.api.serializers.intercorrencia_dre_serializer.unidades_service.get_unidade")
    def test_validacao_campo_motivo_encerramento_dre_obrigatorio_quando_vazio(self, mock_get_unidade):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}

        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "motivo_encerramento_dre": ""
        }

        serializer = IntercorrenciaConclusaoDaDreSerializer(
            instance=self.intercorrencia,
            data=data,
            context={"request": self.request},
            partial=False
        )

        assert not serializer.is_valid()
        assert "detail" in serializer.errors
        assert str(serializer.errors["detail"]).strip() == "motivo_encerramento_dre: Este campo não pode estar em branco."

    @patch("intercorrencias.api.serializers.intercorrencia_dre_serializer.unidades_service.get_unidade")
    def test_validacao_campo_motivo_encerramento_dre_obrigatorio_quando_ausente(self, mock_get_unidade):
        mock_get_unidade.return_value = {"codigo_eol": "123456", "dre_codigo_eol": "654321"}

        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
        }

        serializer = IntercorrenciaConclusaoDaDreSerializer(
            instance=self.intercorrencia,
            data=data,
            context={"request": self.request},
            partial=False
        )

        assert not serializer.is_valid()
        assert "detail" in serializer.errors
        assert str(serializer.errors["detail"]).strip() == "motivo_encerramento_dre: Este campo é obrigatório."

    @patch("intercorrencias.api.serializers.intercorrencia_dre_serializer.unidades_service.get_unidade")
    def test_validacao_campo_motivo_encerramento_dre_valido(self, mock_get_unidade):
        mock_get_unidade.return_value = {
            "codigo_eol": "123456",
            "dre_codigo_eol": "654321"
        }

        self.request.user.unidade_codigo_eol = "123456"

        data = {
            "unidade_codigo_eol": "123456",
            "dre_codigo_eol": "654321",
            "motivo_encerramento_dre": "Encerramento concluído com sucesso"
        }

        serializer = IntercorrenciaConclusaoDaDreSerializer(
            instance=self.intercorrencia,
            data=data,
            context={"request": self.request},
            partial=False
        )

        assert serializer.is_valid(), serializer.errors