import pytest
from datetime import datetime

from freezegun import freeze_time
from django.utils import timezone
from django.core.exceptions import ValidationError

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.tests.factories import IntercorrenciaFactory
from intercorrencias.choices.info_agressor_choices import (
    EtapaEscolar,
)
from intercorrencias.choices.gipe_choices import (
    EnvolveArmaOuAtaque,
    AmeacaFoiRealizadaDeQualManeira,
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
            comunicacao_seguranca_publica="sim", protocolo_acionado="alerta"
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

    def test_booleanos_funcionam(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            notificado_conselho_tutelar=True,
        )
        obj.full_clean()
        assert obj.notificado_conselho_tutelar is True

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

    def test_campos_encerramento_dre(self, intercorrencia_factory):
        dt = timezone.make_aware(datetime(2025, 2, 1, 15, 20))

        obj = intercorrencia_factory(
            finalizado_dre_em=dt,
            finalizado_dre_por="usuario_dre"
        )

        obj.full_clean()
        obj.save()

        obj.refresh_from_db()

        assert obj.finalizado_dre_em == dt
        assert obj.finalizado_dre_por == "usuario_dre"

    def test_pode_ser_editado_por_gipe(self, intercorrencia_factory):
        obj = intercorrencia_factory(status="em_preenchimento_diretor")
        assert obj.pode_ser_editado_por_gipe is True

        obj.status = "em_preenchimento_assistente"
        assert obj.pode_ser_editado_por_gipe is True

        obj.status = "em_preenchimento_dre"
        assert obj.pode_ser_editado_por_gipe is True

        obj.status = "em_preenchimento_gipe"
        assert obj.pode_ser_editado_por_gipe is True

        obj.status = "enviado_para_dre"
        assert obj.pode_ser_editado_por_gipe is True

        obj.status = "enviado_para_gipe"
        assert obj.pode_ser_editado_por_gipe is True

        obj.status = "concluida"
        assert obj.pode_ser_editado_por_gipe is False

    def test_campos_gipe_choices_validos(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            envolve_arma_ataque=EnvolveArmaOuAtaque.SIM,
            ameaca_realizada_qual_maneira=AmeacaFoiRealizadaDeQualManeira.VIRTUALMENTE,
            etapa_escolar=EtapaEscolar.FUNDAMENTAL_ALFABETIZACAO,
        )
        obj.full_clean()
        obj.save()

        assert obj.envolve_arma_ataque == EnvolveArmaOuAtaque.SIM
        assert obj.ameaca_realizada_qual_maneira == AmeacaFoiRealizadaDeQualManeira.VIRTUALMENTE
        assert obj.etapa_escolar == EtapaEscolar.FUNDAMENTAL_ALFABETIZACAO

    def test_campos_gipe_choices_invalidos(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            envolve_arma_ataque="xxx",
            ameaca_realizada_qual_maneira="yyy",
            etapa_escolar="zzz",
        )
        with pytest.raises(ValidationError):
            obj.full_clean()

    def test_campos_gipe_podem_ser_em_branco(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            envolve_arma_ataque="",
            ameaca_realizada_qual_maneira="",
            etapa_escolar="",
            encaminhamentos_gipe="",
        )
        obj.full_clean()

        assert obj.envolve_arma_ataque == ""
        assert obj.ameaca_realizada_qual_maneira == ""
        assert obj.etapa_escolar == ""
        assert obj.encaminhamentos_gipe == ""

    def test_campos_gipe_max_length(self):
        obj = Intercorrencia(
            data_ocorrencia=timezone.now(),
            user_username="usuario",
            unidade_codigo_eol="123456",
            dre_codigo_eol="654321",
            envolve_arma_ataque="x" * 4,
            ameaca_realizada_qual_maneira="x" * 16,
            etapa_escolar="x" * 18,
        )

        with pytest.raises(ValidationError) as exc:
            obj.full_clean()

        err = exc.value.error_dict
        assert "envolve_arma_ataque" in err
        assert "ameaca_realizada_qual_maneira" in err
        assert "etapa_escolar" in err

    def test_campos_gipe_texto_opcionais(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            encaminhamentos_gipe=(
                "Após análise, GIPE recomendou acompanhamento semanal."
            ),
        )

        obj.full_clean()
        obj.save()

        assert "acompanhamento semanal" in obj.encaminhamentos_gipe

    def test_campos_encerramento_gipe(self, intercorrencia_factory):
        dt = timezone.make_aware(datetime(2025, 3, 10, 9, 45))

        obj = intercorrencia_factory(
            finalizado_gipe_em=dt,
            finalizado_gipe_por="usuario_gipe"
        )

        obj.full_clean()
        obj.save()
        obj.refresh_from_db()

        assert obj.finalizado_gipe_em == dt
        assert obj.finalizado_gipe_por == "usuario_gipe"

    def test_campos_encerramento_gipe_podem_ser_em_branco(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            finalizado_gipe_em=None,
            finalizado_gipe_por=""
        )

        obj.full_clean()
        obj.save()
        obj.refresh_from_db()

        assert obj.finalizado_gipe_em is None
        assert obj.finalizado_gipe_por == ""

    def test_status_finalizada(self, intercorrencia_factory):
        obj = intercorrencia_factory(status="finalizada")
        obj.full_clean()
        assert obj.status == "finalizada"

    def test_pode_ser_editado_por_diretor_com_status_finalizada(self, intercorrencia_factory):
        obj = intercorrencia_factory(status="finalizada")
        assert obj.pode_ser_editado_por_diretor is False

    def test_pode_ser_editado_por_dre_com_status_finalizada(self, intercorrencia_factory):
        obj = intercorrencia_factory(status="finalizada")
        assert obj.pode_ser_editado_por_dre is False

    def test_pode_ser_editado_por_gipe_com_status_finalizada(self, intercorrencia_factory):
        obj = intercorrencia_factory(status="finalizada")
        assert obj.pode_ser_editado_por_gipe is True
    
    def test_fora_horario_funcionamento_default(self, intercorrencia_factory):
        obj = intercorrencia_factory()
        assert obj.fora_horario_funcionamento_ue is False
    
    def test_fora_horario_funcionamento_true(self, intercorrencia_factory):
        obj = intercorrencia_factory(fora_horario_funcionamento_ue=True)
        obj.full_clean()
        obj.save()

        assert obj.fora_horario_funcionamento_ue is True
    
    def test_fora_horario_funcionamento_false(self, intercorrencia_factory):
        obj = intercorrencia_factory(fora_horario_funcionamento_ue=False)
        obj.full_clean()
        obj.save()

        assert obj.fora_horario_funcionamento_ue is False

    def test_fora_horario_funcionamento_none(self, intercorrencia_factory):
        obj = intercorrencia_factory(fora_horario_funcionamento_ue=None)
        obj.full_clean()
        obj.save()

        assert obj.fora_horario_funcionamento_ue is None