import pytest
from intercorrencias.models.envolvido import Envolvido

pytestmark = pytest.mark.django_db

def test_criar_envolvido():
    envolvido = Envolvido.objects.create(perfil_dos_envolvidos="Teste Automático")
    assert envolvido.perfil_dos_envolvidos == "Teste Automático"
    assert envolvido.ativo is True
    assert str(envolvido) == "Teste Automático"

def test_perfil_dos_envolvidos_deve_ser_unico():
    Envolvido.objects.create(perfil_dos_envolvidos="Duplicado")
    with pytest.raises(Exception):
        Envolvido.objects.create(perfil_dos_envolvidos="Duplicado")
