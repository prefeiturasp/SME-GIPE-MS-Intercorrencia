import pytest
from datetime import datetime
from django.core.exceptions import ValidationError
from django.utils import timezone
from freezegun import freeze_time

from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.models import Declarante
from intercorrencias.tests.factories import (
    IntercorrenciaFactory,
    DeclaranteFactory,
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
            dre_codigo_eol="1234567",      # > 6
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
        obj = intercorrencia_factory(status='em_preenchimento_diretor')
        assert obj.pode_ser_editado_por_diretor is True

        obj.status = 'concluida'
        assert obj.pode_ser_editado_por_diretor is False

        obj.status = 'em_preenchimento_assistente'
        assert obj.pode_ser_editado_por_diretor is False

    def test_criar_intercorrencia_com_campos_comunicao_protocolo(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            comunicacao_seguranca_publica="sim_gcm",
            protocolo_acionado="ameaca"
        )
        obj.save()
        obj.refresh_from_db()

        assert obj.comunicacao_seguranca_publica == "sim_gcm"
        assert obj.protocolo_acionado == "ameaca"

    def test_relacionamento_declarantes(self, intercorrencia_factory):
        d1 = DeclaranteFactory(declarante="GCM")
        d2 = DeclaranteFactory(declarante="NAAPA")

        obj = intercorrencia_factory()
        obj.declarantes.set([d1, d2])

        assert obj.declarantes.count() == 2
        assert d1 in obj.declarantes.all()
        assert d2 in obj.declarantes.all()

    def test_choices_validos(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            comunicacao_seguranca_publica="sim_pm",
            protocolo_acionado="alerta"
        )
        obj.full_clean()

    def test_choices_invalidos(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            comunicacao_seguranca_publica="valor_invalido",
            protocolo_acionado="outro_invalido"
        )
        with pytest.raises(ValidationError):
            obj.full_clean()

    def test_campos_podem_ser_em_branco(self, intercorrencia_factory):
        obj = intercorrencia_factory(
            comunicacao_seguranca_publica="",
            protocolo_acionado=""
        )
        obj.full_clean()