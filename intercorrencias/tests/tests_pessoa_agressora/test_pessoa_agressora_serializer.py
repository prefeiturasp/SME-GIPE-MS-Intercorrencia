import pytest
from django.db import IntegrityError
from rest_framework import serializers
from intercorrencias.tests.factories import PessoaAgressoraFactory
from intercorrencias.api.serializers.pessoa_agressora_serializer import PessoaAgressoraSerializer


@pytest.mark.django_db
class TestPessoaAgressoraSerializer:
    @pytest.fixture
    def pessoa_agressora(self):
        return PessoaAgressoraFactory(nome="Maria Souza", idade=25)

    def test_serializer_fields(self, pessoa_agressora):
        serializer = PessoaAgressoraSerializer(instance=pessoa_agressora)
        data = serializer.data

        expected_fields = {"uuid", "nome", "idade", "id"}
        assert set(data.keys()) == expected_fields, (
            f"Os campos retornados ({set(data.keys())}) não correspondem "
            f"aos esperados ({expected_fields})"
        )

    def test_field_values(self, pessoa_agressora):
        serializer = PessoaAgressoraSerializer(instance=pessoa_agressora)
        data = serializer.data

        assert data["nome"] == pessoa_agressora.nome
        assert data["idade"] == pessoa_agressora.idade


    def test_valid_data_sem_intercorrencia_falha_no_save(self):
        valid_data = {
            "nome": "Carlos Andrade",
            "idade": 31,
        }

        serializer = PessoaAgressoraSerializer(data=valid_data)

        assert serializer.is_valid(), f"Erros de validação: {serializer.errors}"
        with pytest.raises(IntegrityError):
            serializer.save()
        

    def test_nome_trim(self):
        payload = {
            "nome": "   Ana Clara   ",
            "idade": 22,
        }
        serializer = PessoaAgressoraSerializer(data=payload)

        assert serializer.is_valid(), f"Erros de validação: {serializer.errors}"
        assert serializer.validated_data["nome"] == "Ana Clara"

    def test_nome_vazio_invalido(self):
        payload = {
            "nome": "   ",
            "idade": 22,
        }
        serializer = PessoaAgressoraSerializer(data=payload)

        assert not serializer.is_valid()
        assert "detail" in serializer.errors
        assert "nome:" in serializer.errors["detail"]
        assert "não pode estar em branco" in serializer.errors["detail"]

    def test_validate_nome_em_branco_lanca_erro_customizado(self):
        serializer = PessoaAgressoraSerializer()
        with pytest.raises(serializers.ValidationError, match="O nome não pode estar em branco"):
            serializer.validate_nome("   ")

    def test_idade_none_valida(self):
        payload = {
            "nome": "Pessoa sem idade",
            "idade": None,
        }
        serializer = PessoaAgressoraSerializer(data=payload)

        assert serializer.is_valid(), f"Erros de validação: {serializer.errors}"
        assert serializer.validated_data["idade"] is None

    @pytest.mark.parametrize(
        "idade,mensagem_esperada",
        [
            (0, "A idade deve ser um número positivo."),
            (-1, "maior ou igual a 0"),
        ],
    )
    def test_idade_nao_positiva_invalida(self, idade, mensagem_esperada):
        payload = {
            "nome": "Pessoa Teste",
            "idade": idade,
        }
        serializer = PessoaAgressoraSerializer(data=payload)

        assert not serializer.is_valid()
        assert "detail" in serializer.errors
        assert "idade:" in serializer.errors["detail"]
        assert mensagem_esperada in serializer.errors["detail"]

    def test_is_valid_mantem_detail_quando_ja_existente(self, monkeypatch):
        serializer = PessoaAgressoraSerializer(data={})

        def fake_super_is_valid(_self, raise_exception=False):
            _self._errors = {"detail": "erro já formatado"}
            return False

        monkeypatch.setattr(serializers.ModelSerializer, "is_valid", fake_super_is_valid)

        assert not serializer.is_valid()
        assert serializer.errors == {"detail": "erro já formatado"}

    def test_is_valid_raise_exception_repassa_detail(self):
        payload = {
            "nome": "Pessoa Teste",
            "idade": 0,
        }
        serializer = PessoaAgressoraSerializer(data=payload)

        with pytest.raises(serializers.ValidationError) as exc:
            serializer.is_valid(raise_exception=True)

        assert exc.value.detail["detail"] == "idade: A idade deve ser um número positivo."
