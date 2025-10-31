import pytest

from intercorrencias.models.declarante import Declarante
from intercorrencias.api.serializers.declarante_serializer import DeclaranteSerializer

@pytest.mark.django_db
class TestDeclaranteSerializer:

    @pytest.fixture
    def declarante(self):
        return Declarante.objects.create(declarante="Declarante Exemplo", ativo=True)

    def test_serializer_fields(self, declarante):
        serializer = DeclaranteSerializer(instance=declarante)
        data = serializer.data

        expected_fields = {"uuid", "declarante"}
        assert set(data.keys()) == expected_fields, (
            f"Os campos retornados ({set(data.keys())}) não correspondem "
            f"aos esperados ({expected_fields})"
        )

    def test_field_values(self, declarante):
        serializer = DeclaranteSerializer(instance=declarante)
        data = serializer.data

        assert data["declarante"] == declarante.declarante
        assert str(declarante.uuid) == data["uuid"]

    def test_valid_data_creates_declarante(self):
        valid_data = {"declarante": "Novo Declarante"}
        serializer = DeclaranteSerializer(data=valid_data)

        assert serializer.is_valid(), f"Erros de validação: {serializer.errors}"
        instance = serializer.save()

        assert isinstance(instance, Declarante)
        assert instance.declarante == valid_data["declarante"]
        assert instance.ativo is True or instance.ativo is False

    def test_invalid_data(self):
        serializer = DeclaranteSerializer(data={})
        assert not serializer.is_valid()
        assert "declarante" in serializer.errors