import pytest
from datetime import datetime

from freezegun import freeze_time
from django.utils import timezone
from django.core.exceptions import ValidationError

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.tests.factories import IntercorrenciaFactory
from intercorrencias.choices.info_agressor_choices import (
    MotivoOcorrencia,
    GrupoEtnicoRacial,
    Genero,
    FrequenciaEscolar,
    EtapaEscolar,
)


@pytest.mark.django_db
class TestIntercorrencia:

    def test_criar_intercorrencia_valida(self):
        intercorrencia = IntercorrenciaFactory()
        assert isinstance(intercorrencia, Intercorrencia)
        assert intercorrencia.uuid is not None
        assert intercorrencia.unidade_codigo_eol is not None
        assert intercorrencia.dre_codigo_eol is not None
        assert intercorrencia.user_username is not None

    def test_str_format(self, intercorrencia_factory):
        dt = timezone.make_aware(datetime(2025, 1, 31, 14, 30))
        obj = intercorrencia_factory(
            unidade_codigo_eol="123456",
            data_ocorrencia=dt,
        )
        assert str(obj) == "123456 @ 31/01/2025 14:30"

    def test_atualizado_em_altera_ao_salvar(self, intercorrencia_factory):
        with freeze_time("2025-01-01 10:00:00"):
            obj = intercorrencia_factory()

        criado_em_original = obj.criado_em
        atualizado_em_original = obj.atualizado_em

        # avança 2 minutos; ao salvar, atualizado_em deve mudar
        with freeze_time("2025-01-01 10:02:00"):
            obj.user_username = "novo_usuario"
            obj.save()

        assert obj.criado_em == criado_em_original
        assert obj.atualizado_em > atualizado_em_original

    def test_db_index_flags_nos_campos(self):
        unidade_field = Intercorrencia._meta.get_field("unidade_codigo_eol")
        dre_field = Intercorrencia._meta.get_field("dre_codigo_eol")
        user_field = Intercorrencia._meta.get_field("user_username")

        assert unidade_field.db_index is True
        assert dre_field.db_index is True
        assert user_field.db_index is True

    def test_validacao_max_length(self):
        obj = Intercorrencia(
            data_ocorrencia=timezone.now(),
            user_username="x" * 151,  # > 150
            unidade_codigo_eol="1234567",  # > 6
            dre_codigo_eol="1234567",  # > 6
            sobre_furto_roubo_invasao_depredacao=False,
        )
        with pytest.raises(ValidationError) as exc:
            obj.full_clean()
        err_dict = exc.value.error_dict
        assert "user_username" in err_dict
        assert "unidade_codigo_eol" in err_dict
        assert "dre_codigo_eol" in err_dict

    def test_uuid_unico(self, intercorrencia_factory):
        a = intercorrencia_factory()
        b = intercorrencia_factory()
        assert a.uuid != b.uuid
        assert Intercorrencia.objects.filter(uuid=a.uuid).count() == 1

    def test_pode_ser_editado_por_diretor(self, intercorrencia_factory):
        obj = intercorrencia_factory(status="em_preenchimento_diretor")
        assert obj.pode_ser_editado_por_diretor is True

        obj.status = "concluida"
        assert obj.pode_ser_editado_por_diretor is False

        obj.status = "em_preenchimento_assistente"
        assert obj.pode_ser_editado_por_diretor is False

    def test_criar_intercorrencia_com_campos_comunicacao_protocolo(
        self, intercorrencia_factory
    ):
        obj = intercorrencia_factory(
            comunicacao_seguranca_publica="sim_gcm", protocolo_acionado="ameaca"
        )
        obj.save()
        obj.refresh_from_db()

        assert obj.comunicacao_seguranca_publica == "sim_gcm"
        assert obj.protocolo_acionado == "ameaca"

    def test_choices_validos(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            comunicacao_seguranca_publica="sim_pm", protocolo_acionado="alerta"
        )
        obj.full_clean()

    def test_choices_invalidos(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            comunicacao_seguranca_publica="valor_invalido",
            protocolo_acionado="outro_invalido",
        )
        with pytest.raises(ValidationError):
            obj.full_clean()

    def test_campos_podem_ser_em_branco(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            comunicacao_seguranca_publica="", protocolo_acionado=""
        )
        obj.full_clean()

    def test_choices_info_agressor_validos(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            motivacao_ocorrencia=[MotivoOcorrencia.RACISMO],
            genero_pessoa_agressora=Genero.HOMEM_CIS,
            grupo_etnico_racial=GrupoEtnicoRacial.PARDO,
            etapa_escolar=EtapaEscolar.FUNDAMENTAL_ALFABETIZACAO,
            frequencia_escolar=FrequenciaEscolar.REGULARIZADA,
        )
        obj.full_clean()
        obj.save()

        assert obj.motivacao_ocorrencia == [MotivoOcorrencia.RACISMO]
        assert obj.genero_pessoa_agressora == Genero.HOMEM_CIS
        assert obj.grupo_etnico_racial == GrupoEtnicoRacial.PARDO
        assert obj.etapa_escolar == EtapaEscolar.FUNDAMENTAL_ALFABETIZACAO
        assert obj.frequencia_escolar == FrequenciaEscolar.REGULARIZADA

    def test_choices_info_agressor_invalidos(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            motivacao_ocorrencia=["invalido"],
            genero_pessoa_agressora="errado",
            grupo_etnico_racial="xyz",
            etapa_escolar="errado",
            frequencia_escolar="errado",
        )
        with pytest.raises(ValidationError):
            obj.full_clean()

    def test_campos_texto_opcionais_funcionam(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            nome_pessoa_agressora="João da Silva",
            interacao_ambiente_escolar="Agressor demonstra comportamento reservado.",
            redes_protecao_acompanhamento="CRAS e Conselho Tutelar",
            cep="01234-567",
            logradouro="Rua das Flores",
            numero_residencia="123",
            complemento="Apto 12",
            bairro="Jardim Paulista",
            cidade="São Paulo",
            estado="São Paulo",
        )
        obj.full_clean()
        obj.save()

        assert "João" in obj.nome_pessoa_agressora
        assert "reservado" in obj.interacao_ambiente_escolar
        assert "Conselho Tutelar" in obj.redes_protecao_acompanhamento
        assert obj.cep == "01234-567"
        assert obj.logradouro == "Rua das Flores"
        assert obj.numero_residencia == "123"
        assert obj.complemento == "Apto 12"
        assert obj.bairro == "Jardim Paulista"
        assert obj.cidade == "São Paulo"
        assert obj.estado == "São Paulo"

    def test_campos_endereco_podem_ser_nulos_ou_em_branco(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            cep="",
            logradouro="",
            numero_residencia="",
            complemento="",
            bairro="",
            cidade="",
            estado="",
        )
        obj.full_clean()
        obj.save()

        obj.refresh_from_db()
        assert obj.cep == ""
        assert obj.logradouro == ""
        assert obj.numero_residencia == ""
        assert obj.complemento == ""
        assert obj.bairro == ""
        assert obj.cidade == ""
        assert obj.estado == ""

    def test_validacao_max_length_endereco(self):
        obj = Intercorrencia(
            data_ocorrencia=timezone.now(),
            user_username="usuario",
            unidade_codigo_eol="123456",
            dre_codigo_eol="654321",
            cep="9" * 10,
            logradouro="x" * 256,
            numero_residencia="x" * 11,
            complemento="x" * 101,
            bairro="x" * 101,
            cidade="x" * 101,
            estado="x" * 51,
        )
        with pytest.raises(ValidationError) as exc:
            obj.full_clean()
        err_dict = exc.value.error_dict
        assert "cep" in err_dict
        assert "logradouro" in err_dict
        assert "numero_residencia" in err_dict
        assert "complemento" in err_dict
        assert "bairro" in err_dict
        assert "cidade" in err_dict
        assert "estado" in err_dict

    def test_booleanos_funcionam(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            notificado_conselho_tutelar=True,
            acompanhado_naapa=False,
        )
        obj.full_clean()
        assert obj.notificado_conselho_tutelar is True
        assert obj.acompanhado_naapa is False

    def test_campos_dre(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            acionamento_seguranca_publica=True,
            interlocucao_sts=True,
            info_complementar_sts="Durante a análise da ocorrência de depredação, a STS identificou que os danos ao patrimônio geraram resíduos perigosos",
            interlocucao_cpca=True,
            info_complementar_cpca="Durante as investigações sobre a depredação do patrimônio, a CPCA identificou que entre os envolvidos no ato de vandalismo",
            interlocucao_supervisao_escolar=True,
            info_complementar_supervisao_escolar="Ocorreram 3 incidentes similares no mesmo mês, sempre às quartas-feiras no período vespertino",
            interlocucao_naapa=True,
            info_complementar_naapa="Ocorrido na EMF Jardim Paulista",
        )
        obj.full_clean()
        obj.save()

        assert obj.acionamento_seguranca_publica is True
        assert obj.interlocucao_sts is True
        assert "resíduos perigosos" in obj.info_complementar_sts
        assert obj.interlocucao_cpca is True
        assert "envolvidos no ato" in obj.info_complementar_cpca
        assert obj.interlocucao_supervisao_escolar is True
        assert "quartas-feiras" in obj.info_complementar_supervisao_escolar
        assert obj.interlocucao_naapa is True
        assert "EMF Jardim Paulista" in obj.info_complementar_naapa         
        
        
    def test_pode_ser_editado_por_dre(self, intercorrencia_factory):
        obj = intercorrencia_factory(status="em_preenchimento_dre")
        assert obj.pode_ser_editado_por_dre is True
        
        obj.status = "em_preenchimento_diretor"
        assert obj.pode_ser_editado_por_dre is True
        
        obj.status = "em_preenchimento_assistente"
        assert obj.pode_ser_editado_por_dre is True

        obj.status = "em_preenchimento_gipe"
        assert obj.pode_ser_editado_por_dre is False
        
        obj.status = "concluida"
        assert obj.pode_ser_editado_por_dre is False

