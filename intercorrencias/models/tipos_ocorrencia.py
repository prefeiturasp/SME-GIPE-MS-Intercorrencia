from django.db import models

class TipoOcorrencia(models.Model):
    nome = models.CharField("Tipo de ocorrência", max_length=100, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de Ocorrência"
        verbose_name_plural = "Tipos de Ocorrência"

    def __str__(self):
        return self.nome
