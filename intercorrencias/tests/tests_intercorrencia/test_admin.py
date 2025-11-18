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
    
    @pytest.fixture
    def admin_request(self, rf):
        """Request fake para simular o acesso no admin."""
        request = rf.get("/")
        request.user = None
        return request

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

    def test_fieldsets_exibe_furto_roubo_quando_sim(self, intercorrencia_admin, admin_request):
        """Verifica se a seção correta aparece quando é furto/roubo."""
        obj = Intercorrencia(sobre_furto_roubo_invasao_depredacao=True)
        fieldsets = dict(intercorrencia_admin.get_fieldsets(admin_request, obj))

        assert "Seção É Furto/Roubo (Diretor)" in fieldsets, \
            "A seção de furto/roubo não foi encontrada no fieldsets"

    def test_fieldsets_exibe_nao_furto_quando_nao(self, intercorrencia_admin, admin_request):
        """Verifica se a seção correta aparece quando NÃO é furto/roubo."""
        obj = Intercorrencia(sobre_furto_roubo_invasao_depredacao=False)
        fieldsets = dict(intercorrencia_admin.get_fieldsets(admin_request, obj))

        assert any("Não Furto/Roubo" in nome for nome in fieldsets.keys()), \
        "A seção de não furto/roubo não foi encontrada no fieldsets"

    def test_fieldsets_contem_metadados(self, intercorrencia_admin, admin_request):
        """Garante que a seção de metadados sempre está presente."""
        obj = Intercorrencia()
        fieldsets = dict(intercorrencia_admin.get_fieldsets(admin_request, obj))

        assert "Metadados" in fieldsets, "A seção de Metadados não foi encontrada"

    def test_ordem_das_secoes_fieldsets_furto(self, intercorrencia_admin, admin_request):
        """Verifica a ordem dos fieldsets no caso de furto/roubo."""
        obj = Intercorrencia(sobre_furto_roubo_invasao_depredacao=True)
        fieldsets = intercorrencia_admin.get_fieldsets(admin_request, obj)

        nomes = [titulo for titulo, _ in fieldsets]
        assert nomes == [
            "Seção inicial (Diretor)",
            "Seção É Furto/Roubo (Diretor)",
            "Seção Final (Diretor)",
            "Metadados",
        ], f"Ordem incorreta: {nomes}"

    def test_ordem_das_secoes_fieldsets_nao_furto(self, intercorrencia_admin, admin_request):
        """Verifica a ordem dos fieldsets no caso de não furto/roubo."""
        obj = Intercorrencia(sobre_furto_roubo_invasao_depredacao=False)
        fieldsets = intercorrencia_admin.get_fieldsets(admin_request, obj)

        nomes = [titulo for titulo, _ in fieldsets]
        assert nomes == [
            "Seção inicial (Diretor)",
            "Seção Não Furto/Roubo (Diretor)",
            "Seção Final (Diretor)",
            "Metadados",
        ], f"Ordem incorreta: {nomes}"