import pytest
from intercorrencias.models.tipos_ocorrencia import TipoOcorrencia

pytestmark = pytest.mark.django_db

def test_criar_tipo_ocorrencia():
    tipo = TipoOcorrencia.objects.create(nome="Teste Automático")
    assert tipo.nome == "Teste Automático"
    assert tipo.ativo is True
    assert str(tipo) == "Teste Automático"

def test_nome_deve_ser_unico():
    TipoOcorrencia.objects.create(nome="Duplicado")
    with pytest.raises(Exception):
        TipoOcorrencia.objects.create(nome="Duplicado")
