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

        expected_fields = {"uuid", "nome", "idade", "id", "genero", "grupo_etnico_racial", "etapa_escolar", "frequencia_escolar", "interacao_ambiente_escolar"}
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

    def test_is_valid_mantem_detail_quando_ja_existente(self, monkeypatch):
        serializer = PessoaAgressoraSerializer(data={})

        def fake_super_is_valid(_self, raise_exception=False):
            _self._errors = {"detail": "erro já formatado"}
            return False

        monkeypatch.setattr(serializers.ModelSerializer, "is_valid", fake_super_is_valid)

        assert not serializer.is_valid()
        assert serializer.errors == {"detail": "erro já formatado"}
    
    def test_validate_idade_negativa_lanca_erro(self):
        serializer = PessoaAgressoraSerializer()

        with pytest.raises(serializers.ValidationError, match="A idade deve ser um número positivo."):
            serializer.validate_idade(-5)

    def test_validate_idade_zero_lanca_erro(self):
        serializer = PessoaAgressoraSerializer()

        with pytest.raises(serializers.ValidationError, match="A idade deve ser um número positivo."):
            serializer.validate_idade(0)

    def test_validate_genero_obrigatorio(self):
        serializer = PessoaAgressoraSerializer()

        with pytest.raises(serializers.ValidationError, match="O campo gênero é obrigatório."):
            serializer.validate_genero(None)

    def test_validate_grupo_etnico_racial_obrigatorio(self):
        serializer = PessoaAgressoraSerializer()

        with pytest.raises(serializers.ValidationError, match="O campo grupo étnico racial é obrigatório."):
            serializer.validate_grupo_etnico_racial(None)

    def test_validate_etapa_escolar_obrigatoria(self):
        serializer = PessoaAgressoraSerializer()

        with pytest.raises(serializers.ValidationError, match="A etapa escolar é obrigatória."):
            serializer.validate_etapa_escolar(None)

    def test_validate_frequencia_escolar_obrigatoria(self):
        serializer = PessoaAgressoraSerializer()

        with pytest.raises(serializers.ValidationError, match="A frequência escolar é obrigatória."):
            serializer.validate_frequencia_escolar(None)

    def test_validate_interacao_ambiente_escolar_obrigatoria(self):
        serializer = PessoaAgressoraSerializer()

        with pytest.raises(serializers.ValidationError, match="A interação no ambiente escolar é obrigatória."):
            serializer.validate_interacao_ambiente_escolar(None)
    
    def test_validate_genero_valido(self):
        serializer = PessoaAgressoraSerializer()
        result = serializer.validate_genero("Feminino")

        assert result == "Feminino"

    def test_validate_grupo_etnico_racial_valido(self):
        serializer = PessoaAgressoraSerializer()
        result = serializer.validate_grupo_etnico_racial("Parda")

        assert result == "Parda"

    def test_validate_etapa_escolar_valida(self):
        serializer = PessoaAgressoraSerializer()
        result = serializer.validate_etapa_escolar("Ensino Médio")

        assert result == "Ensino Médio"

    def test_validate_frequencia_escolar_valida(self):
        serializer = PessoaAgressoraSerializer()
        result = serializer.validate_frequencia_escolar("Regular")

        assert result == "Regular"

    def test_validate_interacao_ambiente_escolar_valida(self):
        serializer = PessoaAgressoraSerializer()
        result = serializer.validate_interacao_ambiente_escolar("Boa")

        assert result == "Boa"

    def test_validate_idade_valida(self):
        serializer = PessoaAgressoraSerializer()
        result = serializer.validate_idade(20)

        assert result == 20