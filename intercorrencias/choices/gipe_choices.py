import re
import logging
from django.db import models

from intercorrencias.choices.info_agressor_choices import MotivoOcorrencia

logger = logging.getLogger(__name__)

class EnvolveArmaOuAtaque(models.TextChoices):
    SIM = "sim", "Sim"
    NAO = "nao", "Não"


class AmeacaFoiRealizadaDeQualManeira(models.TextChoices):
    PRESENCIALMENTE = "presencialmente", "Presencialmente"
    VIRTUALMENTE = "virtualmente", "Virtualmente"


class CicloAprendizagem(models.TextChoices):
    ALFABETIZACAO = "alfabetizacao", "Alfabetização (1º ao 3º ano)"
    INTERDISCIPLINAR = "interdisciplinar", "Interdisciplinar (4º ao 6º ano)"
    AUTORAL = "autoral", "Autoral (7º ao 9º ano)"


def get_values_gipe_choices():
    logger.info("Buscando gipe_choices...")
    choices_classes = [
        EnvolveArmaOuAtaque,
        AmeacaFoiRealizadaDeQualManeira,
        MotivoOcorrencia,
        CicloAprendizagem
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