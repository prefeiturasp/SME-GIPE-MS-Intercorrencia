import pytest
from intercorrencias.tests.factories import PessoaAgressoraFactory  

pytestmark = pytest.mark.django_db

def test_criar_pessoa_agressora():
    pessoa = PessoaAgressoraFactory(nome="João Silva", idade=30)
    intercorrencia = pessoa.intercorrencia
    assert intercorrencia is not None
    assert pessoa.nome == "João Silva"
    assert pessoa.idade == 30
    assert str(pessoa) == "João Silva (30 anos)"