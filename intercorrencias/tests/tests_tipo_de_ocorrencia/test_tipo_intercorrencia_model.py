import pytest
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia

pytestmark = pytest.mark.django_db


def test_criar_tipo_ocorrencia():
    tipo = TipoOcorrencia.objects.create(nome="Teste Automático")
    assert tipo.nome == "Teste Automático"
    assert tipo.ativo is True
    assert tipo.tipo_formulario == TipoOcorrencia.TipoChoices.TODOS
    assert tipo.descricao == ""
    assert str(tipo) == "Teste Automático"

def test_nome_deve_ser_unico():
    TipoOcorrencia.objects.create(nome="Duplicado")
    with pytest.raises(Exception):
        TipoOcorrencia.objects.create(nome="Duplicado")

def test_tipo_formulario_choices():
    tipo1 = TipoOcorrencia.objects.create(
        nome="Patrimonial",
        tipo_formulario=TipoOcorrencia.TipoChoices.PATRIMONIAL
    )
    tipo2 = TipoOcorrencia.objects.create(
        nome="Geral",
        tipo_formulario=TipoOcorrencia.TipoChoices.GERAL
    )
    tipo3 = TipoOcorrencia.objects.create(
        nome="Todos",
        tipo_formulario=TipoOcorrencia.TipoChoices.TODOS
    )

    assert tipo1.tipo_formulario == "PATRIMONIAL"
    assert tipo2.tipo_formulario == "GERAL"
    assert tipo3.tipo_formulario == "TODOS"

def test_descricao_pode_ser_vazia():
    tipo = TipoOcorrencia.objects.create(
        nome="Sem descrição",
        descricao=""
    )
    assert tipo.descricao == ""

def test_descricao_pode_ser_preenchida():
    tipo = TipoOcorrencia.objects.create(
        nome="Com descrição",
        descricao="Descrição detalhada"
    )
    assert tipo.descricao == "Descrição detalhada"

def test_ativo_false():
    tipo = TipoOcorrencia.objects.create(
        nome="Inativo",
        ativo=False
    )
    assert tipo.ativo is False

def test_verbose_names():
    assert TipoOcorrencia._meta.verbose_name == "Tipo de Ocorrência"
    assert TipoOcorrencia._meta.verbose_name_plural == "Tipos de Ocorrência"