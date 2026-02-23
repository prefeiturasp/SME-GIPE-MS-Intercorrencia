from django.db import models
from .modelo_base import ModeloBase


class PessoaAgressora(ModeloBase):
    intercorrencia = models.ForeignKey(
        'Intercorrencia',
        on_delete=models.CASCADE,
        related_name='pessoas_agressoras',
        verbose_name="Intercorrência"
    )
    nome = models.CharField(
        max_length=200,
        verbose_name="Nome da pessoa agressora"
    )
    idade = models.PositiveIntegerField(
        verbose_name="Idade da pessoa agressora",
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = "Pessoa Agressora"
        verbose_name_plural = "Pessoas Agressoras"
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} ({self.idade} anos)" if self.idade else self.nome