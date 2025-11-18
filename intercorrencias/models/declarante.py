from django.db import models
from .modelo_base import ModeloBase

class Declarante(ModeloBase):
    declarante = models.CharField("Declarante", max_length=100, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Declarante"
        verbose_name_plural = "Declarantes"

    def __str__(self):
        return self.declarante