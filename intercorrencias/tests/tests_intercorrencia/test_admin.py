import pytest
from django.contrib.admin.sites import AdminSite

from intercorrencias.admin import IntercorrenciaAdmin, TipoOcorrenciaAdmin
from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia
from intercorrencias.tests.factories import (
    IntercorrenciaFactory,
    TipoOcorrenciaFactory
)

@pytest.mark.django_db
class TestIntercorrenciaAdmin:
    @pytest.fixture
    def admin_site(self):
        return AdminSite()

    @pytest.fixture
    def intercorrencia_admin(self, admin_site):
        return IntercorrenciaAdmin(Intercorrencia, admin_site)

    @pytest.fixture
    def tipo_ocorrencia_admin(self, admin_site):
        return TipoOcorrenciaAdmin(TipoOcorrencia, admin_site)

    def test_get_tipos_ocorrencia_com_tipos(self, intercorrencia_admin):
        """Testa o método get_tipos_ocorrencia que formata a exibição dos tipos no admin - LINHA 28"""
        tipo1 = TipoOcorrenciaFactory(nome="Furto")
        tipo2 = TipoOcorrenciaFactory(nome="Roubo")
        
        intercorrencia = IntercorrenciaFactory()
        intercorrencia.tipos_ocorrencia.add(tipo1, tipo2)
        
        result = intercorrencia_admin.get_tipos_ocorrencia(intercorrencia)
        
        assert "Furto" in result
        assert "Roubo" in result
        assert result == "Roubo, Furto"

    def test_get_tipos_ocorrencia_sem_tipos(self, intercorrencia_admin):
        """Testa o método get_tipos_ocorrencia quando não há tipos associados"""
        intercorrencia = IntercorrenciaFactory()
        
        result = intercorrencia_admin.get_tipos_ocorrencia(intercorrencia)
        
        assert result == ""

    def test_get_tipos_ocorrencia_apenas_um_tipo(self, intercorrencia_admin):
        """Testa o método get_tipos_ocorrencia com apenas um tipo associado"""
        tipo = TipoOcorrenciaFactory(nome="Invasão")
        intercorrencia = IntercorrenciaFactory()
        intercorrencia.tipos_ocorrencia.add(tipo)
        
        result = intercorrencia_admin.get_tipos_ocorrencia(intercorrencia)
        
        assert result == "Invasão"

    def test_intercorrencia_admin_configuracoes(self, intercorrencia_admin):
        """Testa as configurações básicas do IntercorrenciaAdmin"""
        assert intercorrencia_admin.list_display == (
            "user_username",
            "unidade_codigo_eol",
            "dre_codigo_eol",
            "sobre_furto_roubo_invasao_depredacao",
            "criado_em",
        )
        assert intercorrencia_admin.list_filter == (
            "user_username", 
            "unidade_codigo_eol", 
            "dre_codigo_eol", 
            "sobre_furto_roubo_invasao_depredacao", 
        )
        assert intercorrencia_admin.search_fields == (
            "unidade_codigo_eol", 
            "user_username", 
            "dre_codigo_eol"
        )
        assert intercorrencia_admin.readonly_fields == (
            "uuid", 
            "criado_em", 
            "atualizado_em"
        )
        assert intercorrencia_admin.ordering == ("-criado_em",)

    def test_tipo_ocorrencia_admin_configuracoes(self, tipo_ocorrencia_admin):
        assert tipo_ocorrencia_admin.list_display == ("nome", "ativo")
        assert tipo_ocorrencia_admin.search_fields == ("nome",)
        assert tipo_ocorrencia_admin.list_filter == ("ativo",)

    def test_fieldsets_existe_secao_final(self, intercorrencia_admin):
        fieldsets = dict(intercorrencia_admin.fieldsets)
        assert "Seção Final (Diretor)" in fieldsets, "A seção final não foi encontrada no fieldsets"

    def test_campos_secao_final_estao_presentes(self, intercorrencia_admin):
        fieldsets = dict(intercorrencia_admin.fieldsets)
        secao_final = fieldsets.get("Seção Final (Diretor)")
        campos = secao_final.get("fields", [])
        assert "declarante" in campos
        assert "comunicacao_seguranca_publica" in campos
        assert "protocolo_acionado" in campos

    def test_ordem_das_secoes_fieldsets(self, intercorrencia_admin):
        nomes_secoes = [titulo for titulo, _ in intercorrencia_admin.fieldsets]
        assert nomes_secoes == [
            "Seção inicial (Diretor)",
            "Seção Furto/Roubo (Diretor)",
            "Seção Final (Diretor)",
            "Metadados",
        ]