import pytest
from django.utils import timezone
from intercorrencias.api.serializers.intercorrencia_serializer import IntercorrenciaSerializer
from intercorrencias.models.intercorrencia import Intercorrencia
from intercorrencias.services import unidades_service


@pytest.mark.django_db
def test_serializer_valido_caminho_feliz(monkeypatch):
    """
    Deve validar quando unidade existe e a DRE informada corresponde à DRE da unidade.
    """
    # Arrange: mock do serviço externo
    def fake_get_unidade_ok(codigo_unidade):
        return {"codigo_eol": codigo_unidade, "dre_codigo_eol": "654321"}

    class FakeExternalServiceError(Exception):
        pass

    # Monkeypatch do módulo usado pelo serializer
    import intercorrencias.api.serializers.intercorrencia_serializer as mod
    monkeypatch.setattr(mod, "unidades_service", type("S", (), {
        "get_unidade": staticmethod(fake_get_unidade_ok),
        "ExternalServiceError": FakeExternalServiceError
    }))

    payload = {
        "data_ocorrencia": timezone.now().isoformat(),
        "unidade_codigo_eol": "123456",
        "dre_codigo_eol": "654321",
        "sobre_furto_roubo_invasao_depredacao": True,
        # Tentativa de incluir campo read-only deve ser ignorada:
        "user_username": "nao_deveria_entrar",
    }

    # Act
    ser = IntercorrenciaSerializer(data=payload)
    assert ser.is_valid(), ser.errors
    validated = ser.validated_data

    # Assert
    assert validated["unidade_codigo_eol"] == "123456"
    assert validated["dre_codigo_eol"] == "654321"
    assert validated["sobre_furto_roubo_invasao_depredacao"] is True
    # read_only_fields: não deve estar em validated_data
    assert "user_username" not in validated

    # Opcional: criar o objeto
    obj = ser.save(user_username="será_definido_pelo_jwt")
    assert isinstance(obj, Intercorrencia)
    assert obj.user_username == "será_definido_pelo_jwt"


@pytest.mark.django_db
def test_unidade_nao_encontrada(monkeypatch):
    """
    Quando o serviço retorna None ou código divergente, deve falhar em unidade_codigo_eol.
    """
    def fake_get_unidade_none(codigo_unidade):
        return None

    class FakeExternalServiceError(Exception):
        pass

    import intercorrencias.api.serializers.intercorrencia_serializer as mod
    monkeypatch.setattr(mod, "unidades_service", type("S", (), {
        "get_unidade": staticmethod(fake_get_unidade_none),
        "ExternalServiceError": FakeExternalServiceError
    }))

    ser = IntercorrenciaSerializer(data={
        "data_ocorrencia": timezone.now().isoformat(),
        "unidade_codigo_eol": "999999",
        "dre_codigo_eol": "654321",
        "sobre_furto_roubo_invasao_depredacao": False,
    })

    assert not ser.is_valid()
    assert "unidade_codigo_eol" in ser.errors
    assert ser.errors["unidade_codigo_eol"][0] in [
        "Unidade não encontrada.",
        # caso a mensagem do serviço seja usada
        # "Serviço indisponível", etc.
    ]


@pytest.mark.django_db
def test_dre_divergente(monkeypatch):
    """
    Quando a DRE informada não corresponde à DRE da unidade, deve falhar em dre_codigo_eol.
    """
    def fake_get_unidade_ok(codigo_unidade):
        return {"codigo_eol": codigo_unidade, "dre_codigo_eol": "111111"}

    class FakeExternalServiceError(Exception):
        pass

    import intercorrencias.api.serializers.intercorrencia_serializer as mod
    monkeypatch.setattr(mod, "unidades_service", type("S", (), {
        "get_unidade": staticmethod(fake_get_unidade_ok),
        "ExternalServiceError": FakeExternalServiceError
    }))

    ser = IntercorrenciaSerializer(data={
        "data_ocorrencia": timezone.now().isoformat(),
        "unidade_codigo_eol": "123456",
        "dre_codigo_eol": "654321",  # diverge do "111111" retornado pelo serviço
        "sobre_furto_roubo_invasao_depredacao": False,
    })

    assert not ser.is_valid()
    assert "dre_codigo_eol" in ser.errors
    assert ser.errors["dre_codigo_eol"][0] == "DRE informada não corresponde à DRE da unidade."


@pytest.mark.django_db
def test_erro_servico_externo_monkeypatch(monkeypatch):
    """
    Se o serviço levantar ExternalServiceError, deve mapear para ValidationError em unidade_codigo_eol.
    """
    class FakeExternalServiceError(Exception):
        pass

    def fake_get_unidade_raise(_):
        raise FakeExternalServiceError("Serviço indisponível no momento")

    import intercorrencias.api.serializers.intercorrencia_serializer as mod
    monkeypatch.setattr(mod, "unidades_service", type("S", (), {
        "get_unidade": staticmethod(fake_get_unidade_raise),
        "ExternalServiceError": FakeExternalServiceError
    }))

    ser = IntercorrenciaSerializer(data={
        "data_ocorrencia": timezone.now().isoformat(),
        "unidade_codigo_eol": "123456",
        "dre_codigo_eol": "654321",
        "sobre_furto_roubo_invasao_depredacao": False,
    })

    assert not ser.is_valid()
    assert "unidade_codigo_eol" in ser.errors
    # mensagem vem do Exception original
    assert "Serviço indisponível" in ser.errors["unidade_codigo_eol"][0]


@pytest.mark.django_db
def test_dre_erro_quando_nao_enviada(monkeypatch):
    """
    Se codigo_dre não for enviado, valida mesmo assim (o serializer só compara quando informado).
    """

    class FakeExternalServiceError(Exception):
        pass

    import intercorrencias.api.serializers.intercorrencia_serializer as mod
    monkeypatch.setattr(mod, "unidades_service", type("S", (), {
        "get_unidade": "999999",
        "ExternalServiceError": FakeExternalServiceError
    }))

    ser = IntercorrenciaSerializer(data={
        "data_ocorrencia": timezone.now().isoformat(),
        "unidade_codigo_eol": "777777",
        # "dre_codigo_eol" ausente de propósito
        "sobre_furto_roubo_invasao_depredacao": False,
    })

    assert not ser.is_valid()
    assert "dre_codigo_eol" in ser.errors
    assert ser.errors["dre_codigo_eol"][0] == "Este campo é obrigatório."


@pytest.mark.django_db
def test_read_only_fields_ignora_user_username_no_input(monkeypatch):
    """
    Mesmo enviando user_username no payload, não entra em validated_data (é read-only).
    """
    def fake_get_unidade_ok(codigo_unidade):
        return {"codigo_eol": codigo_unidade, "dre_codigo_eol": "333333"}

    class FakeExternalServiceError(Exception):
        pass

    import intercorrencias.api.serializers.intercorrencia_serializer as mod
    monkeypatch.setattr(mod, "unidades_service", type("S", (), {
        "get_unidade": staticmethod(fake_get_unidade_ok),
        "ExternalServiceError": FakeExternalServiceError
    }))

    payload = {
        "data_ocorrencia": timezone.now().isoformat(),
        "unidade_codigo_eol": "333333",
        "dre_codigo_eol": "333333",
        "sobre_furto_roubo_invasao_depredacao": False,
        "user_username": "hacker_tentando_inserir",
    }
    ser = IntercorrenciaSerializer(data=payload)
    assert ser.is_valid(), ser.errors
    assert "user_username" not in ser.validated_data

    obj = ser.save(user_username="definido_pelo_contexto_jwt")
    assert obj.user_username == "definido_pelo_contexto_jwt"