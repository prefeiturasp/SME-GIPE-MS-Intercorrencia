from django.db import models
from .modelo_base import ModeloBase
from intercorrencias.choices.info_agressor_choices import (
    GrupoEtnicoRacial,
    Genero,
    FrequenciaEscolar,
    EtapaEscolar,
)


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
    idade_em_meses = models.BooleanField(
        verbose_name="A idade está em meses?",
        default=False,
        blank=True,
        null=True,
    )
    genero = models.CharField(
        max_length=18,
        choices=Genero.choices,
        verbose_name="Qual gênero?",
        blank=True,
    )
    grupo_etnico_racial = models.CharField(
        max_length=15,
        choices=GrupoEtnicoRacial.choices,
        verbose_name="Qual grupo étnico-racial?",
        blank=True,
    )
    etapa_escolar = models.CharField(
        max_length=27,
        choices=EtapaEscolar.choices,
        verbose_name="Qual etapa escolar?",
        blank=True,
    )
    frequencia_escolar = models.CharField(
        max_length=23,
        choices=FrequenciaEscolar.choices,
        verbose_name="Qual a frequência escolar?",
        blank=True,
    )
    interacao_ambiente_escolar = models.TextField(
        verbose_name="Como é a interação da pessoa no ambiente escolar?",
        blank=True,
    )
    nacionalidade = models.CharField(
        max_length=100,
        verbose_name="A nacionalidade corresponde ao país de nascimento.",
        blank=True,
    )
    pessoa_com_deficiencia = models.BooleanField(
        verbose_name="Pessoa com deficiência?",
        default=False,
        blank=True,
        null=True,
    )
    
    class Meta:
        verbose_name = "Pessoa Agressora"
        verbose_name_plural = "Pessoas Agressoras"
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} ({self.idade} anos)" if self.idade else self.nome