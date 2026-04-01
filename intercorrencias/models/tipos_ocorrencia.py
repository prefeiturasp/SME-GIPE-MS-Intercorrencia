from django.db import models
from .modelo_base import ModeloBase


class TipoOcorrencia(ModeloBase):

    class TipoChoices(models.TextChoices):
        PATRIMONIAL = "PATRIMONIAL", "Patrimonial"
        GERAL = "GERAL", "Geral"
        TODOS = "TODOS", "Todos"

    nome = models.CharField("Tipo de ocorrência", max_length=100, unique=True)
    tipo_formulario = models.CharField(
        "Tipo de Formulário",
        max_length=20,
        choices=TipoChoices.choices,
        default=TipoChoices.TODOS
    )
    descricao = models.TextField(
        verbose_name="Descrição do tipo de ocorrência",
        help_text="Descreva o tipo de ocorrência, para que ele possa ser identificado e diferenciado dos outros tipos.",
        blank=True,
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tipo de Ocorrência"
        verbose_name_plural = "Tipos de Ocorrência"

    def __str__(self):
        return self.nome