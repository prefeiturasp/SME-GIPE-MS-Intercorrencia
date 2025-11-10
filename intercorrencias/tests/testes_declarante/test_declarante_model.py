import pytest
from django.db import IntegrityError

from intercorrencias.models.declarante import Declarante

@pytest.mark.django_db
def test_criacao_declarante():
    declarante = Declarante.objects.create(declarante="João Silva")
    assert declarante.declarante == "João Silva"
    assert declarante.ativo is True
    assert str(declarante) == "João Silva"

@pytest.mark.django_db
def test_declarante_unico():
    Declarante.objects.create(declarante="Maria")
    with pytest.raises(IntegrityError):
        Declarante.objects.create(declarante="Maria")

@pytest.mark.django_db
def test_valores_padrao_declarante():
    declarante = Declarante.objects.create(declarante="Carlos")
    assert declarante.ativo is True

@pytest.mark.django_db
def test_verbose_names_declarante():
    verbose_name = Declarante._meta.verbose_name
    verbose_name_plural = Declarante._meta.verbose_name_plural
    assert verbose_name == "Declarante"
    assert verbose_name_plural == "Declarantes"