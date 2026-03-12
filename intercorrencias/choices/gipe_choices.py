import re
import logging
from django.db import models

from intercorrencias.choices.info_agressor_choices import MotivoOcorrencia, EtapaEscolar

logger = logging.getLogger(__name__)

class EnvolveArmaOuAtaque(models.TextChoices):
    SIM = "sim", "Sim"
    NAO = "nao", "Não"


class AmeacaFoiRealizadaDeQualManeira(models.TextChoices):
    PRESENCIALMENTE = "presencialmente", "Presencialmente"
    VIRTUALMENTE = "virtualmente", "Virtualmente"


def get_values_gipe_choices():
    logger.info("Buscando gipe_choices...")
    choices_classes = [
        EnvolveArmaOuAtaque,
        AmeacaFoiRealizadaDeQualManeira,
        MotivoOcorrencia,
        EtapaEscolar
    ]

    def to_snake_case(name: str) -> str:
        return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    return {
        to_snake_case(cls.__name__): [
            {"value": choice.value, "label": choice.label}
            for choice in cls
        ]
        for cls in choices_classes
    }