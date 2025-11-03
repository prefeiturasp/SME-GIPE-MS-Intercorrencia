from django.db import models
from .modelo_base import ModeloBase

class Intercorrencia(ModeloBase):

    STATUS_CHOICES = [
        ("em_preenchimento_diretor", "Em preenchimento - Diretor"),
    ]

    STATUS_EXTRA_LABELS = {
        "em_preenchimento_diretor": "Incompleta",
    }

    SMART_SAMPA_CHOICES = [
        ("sim_com_dano", "Sim e houve dano"),
        ("sim_sem_dano", "Sim, mas não houve dano"),
        ("nao_faz_parte", "A UE não faz parte do Smart Sampa"),
    ]

    SEGURANCA_PUBLICA_CHOICES = [
        ("sim_gcm", "Sim, com GCM"),
        ("sim_pm", "Sim, com a PM"),
        ("nao", "Não"),
    ]

    PROTOCOLO_CHOICES = [
        ("ameaca", "Ameaça"),
        ("alerta", "Alerta"),
        ("registro", "Apenas para registro/ não se aplica"),
    ]

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
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="em_preenchimento_diretor",
        verbose_name="Status da Intercorrência",
    )
    tipos_ocorrencia = models.ManyToManyField(
        "intercorrencias.TipoOcorrencia",
        verbose_name="Tipos de Ocorrência",
        help_text="Selecione um ou mais tipos de ocorrência",
        blank=True,
    )
    descricao_ocorrencia = models.TextField(
        verbose_name="Descrição da Ocorrência",
        help_text="Descreva o fato ocorrido, incluindo informações sobre agressores, vítimas e prejuízos.",
        blank=True,
    )
    smart_sampa_situacao = models.CharField(
        max_length=20,
        choices=SMART_SAMPA_CHOICES,
        verbose_name="UE é contemplada pelo Smart Sampa? Houve dano às câmeras?",
        blank=True,
    )
    declarante = models.ForeignKey(
        "intercorrencias.Declarante",
        on_delete=models.SET_NULL,
        verbose_name="Quem é o declarante",
        help_text="Selecione quem está declarando a intercorrência",
        blank=True,
        null=True,
    )
    comunicacao_seguranca_publica = models.CharField(
        max_length=20,
        choices=SEGURANCA_PUBLICA_CHOICES,
        verbose_name="Houve comunicação com a segurança pública?",
        blank=True,
    )
    protocolo_acionado = models.CharField(
        max_length=20,
        choices=PROTOCOLO_CHOICES,
        verbose_name="Qual protocolo foi acionado?",
        blank=True,
    )

    class Meta:
        ordering = ("-criado_em",)

    def __str__(self) -> str:
        return f"{self.unidade_codigo_eol} @ {self.data_ocorrencia:%d/%m/%Y %H:%M}"
    
    @property
    def pode_ser_editado_por_diretor(self):
        """Verifica se ainda pode ser editado pelo diretor"""
        return self.status == 'em_preenchimento_diretor'