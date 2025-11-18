from django.db import models
from .modelo_base import ModeloBase

class Envolvido(ModeloBase):
    perfil_dos_envolvidos= models.CharField("Envolvidos", max_length=30, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Envolvido"
        verbose_name_plural = "Envolvidos"

    def __str__(self):
        return self.perfil_dos_envolvidos
