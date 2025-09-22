import uuid
from django.db import models

class ModeloBase(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Intercorrencia(ModeloBase):
    data_ocorrencia = models.DateTimeField(
        verbose_name="Data e Hora da Ocorrência",
        help_text="Data e hora em que a intercorrência ocorreu"
    )
    user_username = models.CharField(
        max_length=150, db_index=True,
        verbose_name="Username do Usuário",
        help_text="Username do usuário que está registrando a ocorrência",
    )
    unidade_codigo_eol = models.CharField(
        max_length=6, db_index=True,
        verbose_name="Código EOL da Unidade",
        help_text="Código EOL da unidade onde ocorreu a intercorrência",
    )
    dre_codigo_eol = models.CharField(
        max_length=6, db_index=True,
        verbose_name="Código EOL da DRE",
        help_text="Código EOL da DRE responsável pela unidade",
    )
    sobre_furto_roubo_invasao_depredacao = models.BooleanField(
        "É sobre furto, roubo, invasão ou depredação?",
        default=False
    )

    class Meta:
        ordering = ("-criado_em",)

    def __str__(self) -> str:
        return f"{self.unidade_codigo_eol} @ {self.data_ocorrencia:%d/%m/%Y %H:%M}"
