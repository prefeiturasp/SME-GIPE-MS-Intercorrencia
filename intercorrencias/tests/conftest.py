import os
import pytest
from intercorrencias.tests.factories import IntercorrenciaFactory
from pytest_factoryboy import register
from django.test import Client

@pytest.fixture
def client():
    return Client()

# Garante que o Django use o settings do projeto quando rodar isolado
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

register(IntercorrenciaFactory)


@pytest.fixture(autouse=True)
def _media_settings(tmp_path, settings):
    # se futuramente tiver FileFields, isola mídia nos testes
    settings.MEDIA_ROOT = tmp_path / "media"
    return settings
