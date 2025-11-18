import uuid
import pytest

from rest_framework import serializers
from intercorrencias.api.serializers.verify_intercorrencia_serializer import UUIDInputSerializer


class TestUUIDInputSerializer:
    def test_valid_uuid_as_string(self):
        valid_uuid = str(uuid.uuid4())
        serializer = UUIDInputSerializer(data={"uuid": valid_uuid})

        assert serializer.is_valid() is True
        assert serializer.validated_data["uuid"] == uuid.UUID(valid_uuid)

    def test_valid_uuid_as_object(self):
        valid_uuid = uuid.uuid4()
        serializer = UUIDInputSerializer(data={"uuid": valid_uuid})

        assert serializer.is_valid() is True
        assert serializer.validated_data["uuid"] == valid_uuid

    def test_missing_uuid_field_returns_error(self):
        serializer = UUIDInputSerializer(data={})
        assert serializer.is_valid() is False
        assert "detail" in serializer.errors
        assert "uuid" in serializer.errors["detail"]
        assert "obrigatório" in serializer.errors["detail"].lower()

    def test_raise_exception_on_invalid_uuid(self):
        serializer = UUIDInputSerializer(data={"uuid": "xxx"})
        with pytest.raises(serializers.ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)

        error_data = excinfo.value.detail
        assert isinstance(error_data, dict)
        assert "detail" in error_data
        assert "uuid" in error_data["detail"]