from django.db import models
from django.contrib.postgres.fields import ArrayField
from .modelo_base import ModeloBase

from intercorrencias.choices.info_agressor_choices import (
    MotivoOcorrencia,
    GrupoEtnicoRacial,
    Genero,
    FrequenciaEscolar,
    EtapaEscolar,
)

from intercorrencias.choices.gipe_choices import (
    EnvolveArmaOuAtaque,
    AmeacaFoiRealizadaDeQualManeira,
    CicloAprendizagem
)


class Intercorrencia(ModeloBase):

    STATUS_CHOICES = [
        ("em_preenchimento_diretor", "Em preenchimento - Diretor"),
        ("enviado_para_dre", "Enviado para DRE"),
        ("enviado_para_gipe", "Enviado para GIPE"),
        ("finalizada", "Finalizada"),
    ]

    STATUS_EXTRA_LABELS = {
        "em_preenchimento_diretor": "Incompleta",
        "enviado_para_dre": "Em andamento",
        "enviado_para_gipe": "Em andamento",
        "finalizada": "Finalizada",
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

    INFORMACOES_AGRESSOR_VITIMA_CHOICES = [
        ("sim", "Sim"),
        ("nao", "Não"),
    ]

    data_ocorrencia = models.DateTimeField(
        verbose_name="Data e Hora da Ocorrência",
        help_text="Data e hora em que a intercorrência ocorreu",
    )
    user_username = models.CharField(
        max_length=150,
        db_index=True,
        verbose_name="Username do Usuário",
        help_text="Username do usuário que está registrando a ocorrência",
    )
    unidade_codigo_eol = models.CharField(
        max_length=6,
        db_index=True,
        verbose_name="Código EOL da Unidade",
        help_text="Código EOL da unidade onde ocorreu a intercorrência",
    )
    dre_codigo_eol = models.CharField(
        max_length=6,
        db_index=True,
        verbose_name="Código EOL da DRE",
        help_text="Código EOL da DRE responsável pela unidade",
    )
    sobre_furto_roubo_invasao_depredacao = models.BooleanField(
        "É sobre furto, roubo, invasão ou depredação?", default=False
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
        on_delete=models.PROTECT,
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
    envolvido = models.ForeignKey(
        "intercorrencias.Envolvido",
        verbose_name="Quem são os envolvidos?",
        blank=True,
        null=True,
        on_delete=models.PROTECT,
        help_text="Selecione quem são os envolvidos",
    )
    tem_info_agressor_ou_vitima = models.CharField(
        max_length=3,
        choices=INFORMACOES_AGRESSOR_VITIMA_CHOICES,
        verbose_name="Existem informações sobre o agressor e/ou vítima?",
        blank=True,
    )
    nome_pessoa_agressora = models.CharField(
        max_length=200,
        verbose_name="Qual o nome da pessoa agressora?",
        blank=True,
    )
    idade_pessoa_agressora = models.PositiveIntegerField(
        verbose_name="Qual a idade da pessoa agressora?", blank=True, null=True
    )
    motivacao_ocorrencia = ArrayField(
        models.CharField(max_length=23, choices=MotivoOcorrencia.choices),
        verbose_name="O que motivou a ocorrência?",
        blank=True,
        default=list,  # Lista vazia como padrão
        help_text="Selecione uma ou mais motivações"
    )
    genero_pessoa_agressora = models.CharField(
        max_length=18,
        choices=Genero.choices,
        verbose_name="Qual gênero?",
        blank=True,
    )
    grupo_etnico_racial = models.CharField(
        max_length=8,
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
        verbose_name="Como é a interação da pessoa agressora no ambiente escolar?",
        blank=True,
    )
    redes_protecao_acompanhamento = models.TextField(
        verbose_name="Quais redes de proteção estão acompanhando o caso?",
        blank=True,
    )
    notificado_conselho_tutelar = models.BooleanField(
        verbose_name="A ocorrência foi notificada ao Conselho Tutelar?",
        default=False,
        blank=True,
        null=True,
    )
    acompanhado_naapa = models.BooleanField(
        verbose_name="A ocorrência foi acompanhada pelo NAAPA?",
        default=False,
        blank=True,
        null=True,
    )
    cep = models.CharField(
        max_length=9,
        verbose_name="CEP",
        help_text="CEP do endereço relacionado à intercorrência",
        blank=True,
    )
    logradouro = models.CharField(
        max_length=255,
        verbose_name="Logradouro",
        help_text="Rua, avenida ou local da ocorrência",
        blank=True,
    )
    numero_residencia = models.CharField(
        max_length=10,
        verbose_name="Número da residência",
        help_text="Número do imóvel onde ocorreu a intercorrência",
        blank=True,
    )
    complemento = models.CharField(
        max_length=100,
        verbose_name="Complemento",
        help_text="Complemento do endereço (ex: bloco, apartamento, referência)",
        blank=True,
    )
    bairro = models.CharField(
        max_length=100,
        verbose_name="Bairro",
        help_text="Bairro do endereço da ocorrência",
        blank=True,
    )
    cidade = models.CharField(
        max_length=100,
        verbose_name="Cidade",
        help_text="Cidade onde ocorreu a intercorrência",
        blank=True,
    )
    estado = models.CharField(
        max_length=50,
        verbose_name="Estado",
        help_text="Nome do estado por extenso (ex: São Paulo, Rio de Janeiro)",
        blank=True,
    )
    motivo_encerramento_ue=models.TextField(
        verbose_name="Motivo do encerramento pela UE",
        blank=True,
    )
    protocolo_da_intercorrencia=models.CharField(
        max_length=100,
        verbose_name="Protocolo da Intercorrência",
        blank=True,
    )
    finalizado_diretor_em = models.DateTimeField(
        verbose_name="Finalizado pelo Diretor em",
        blank=True, null=True
    )
    finalizado_diretor_por = models.CharField(
        max_length=150,
        verbose_name="Finalizado pelo Diretor por",
        blank=True
    )
    acionamento_seguranca_publica = models.BooleanField(
        verbose_name="Houve acionamento da Secretaria de Segurança Pública ou Forças de Segurança?",
        default=False,
        blank=True,
        null=True,
    )
    interlocucao_sts = models.BooleanField(
        verbose_name="Houve interlocução com a Supervisão Técnica de Saúde (STS)?",
        default=False,
        blank=True,
        null=True,
    )
    info_complementar_sts = models.TextField(
        verbose_name="Informação complementar da atuação conjunta entre DRE e STS",
        blank=True,
    )
    interlocucao_cpca = models.BooleanField(
        verbose_name="Houve interlocução com a Coordenação de Políticas para Criança e Adolescente (CPCA)?",
        default=False,
        blank=True,
        null=True,
    )
    info_complementar_cpca = models.TextField(
        verbose_name="Informação complementar da atuação conjunta entre DRE e CPCA",
        blank=True,
    )
    interlocucao_supervisao_escolar = models.BooleanField(
        verbose_name="Houve interlocução com a Supervisão Escolar?",
        default=False,
        blank=True,
        null=True, 
    )
    info_complementar_supervisao_escolar = models.TextField(
        verbose_name="Informação complementar da atuação conjunta entre DRE e Supervisão Escolar",
        blank=True,
    )
    interlocucao_naapa = models.BooleanField(
        verbose_name="Houve interlocução com o Núcleo de Apoio e Acompanhamento para a Aprendizagem (NAAPA)?",
        default=False,
        blank=True,
        null=True,
    )
    info_complementar_naapa = models.TextField(
        verbose_name="Informação complementar da atuação conjunta entre DRE e NAAPA",
        blank=True,
    )
    motivo_encerramento_dre=models.TextField(
        verbose_name="Motivo do encerramento DRE",
        blank=True,
    )
    finalizado_dre_em = models.DateTimeField(
        verbose_name="Finalizado DRE em",
        blank=True, null=True
    )
    finalizado_dre_por = models.CharField(
        max_length=150,
        verbose_name="Finalizado DRE por",
        blank=True
    )
    envolve_arma_ataque = models.CharField(
        max_length=3,
        choices=EnvolveArmaOuAtaque.choices,
        verbose_name="Envolve arma ou ataque?",
        blank=True,
    )
    ameaca_realizada_qual_maneira = models.CharField(
        max_length=15,
        choices=AmeacaFoiRealizadaDeQualManeira.choices,
        verbose_name="Ameaça foi realizada de qual maneira?",
        blank=True,
    )
    qual_ciclo_aprendizagem = models.CharField(
        max_length=17,
        choices=CicloAprendizagem.choices,
        verbose_name="Qual o ciclo de aprendizagem?",
        blank=True,
    )
    info_sobre_interacoes_virtuais_pessoa_agressora = models.TextField(
        verbose_name="Existe informações sobre as interações virtuais da pessoa agressora?",
        blank=True,
    )
    encaminhamentos_gipe = models.TextField(
        verbose_name="São informações após a análise feita pelo GIPE.",
        blank=True,
    )
    motivo_encerramento_gipe=models.TextField(
        verbose_name="Motivo do encerramento GIPE",
        blank=True,
    )
    finalizado_gipe_em = models.DateTimeField(
        verbose_name="Finalizado GIPE em",
        blank=True, null=True
    )
    finalizado_gipe_por = models.CharField(
        max_length=150,
        verbose_name="Finalizado GIPE por",
        blank=True
    )

    class Meta:
        ordering = ("-criado_em",)

    def __str__(self) -> str:
        return f"{self.unidade_codigo_eol} @ {self.data_ocorrencia:%d/%m/%Y %H:%M}"

    @staticmethod
    def gerar_protocolo():
        """
        Gera um protocolo único no formato: GIPE-2025/XXXXXXXXXXXXX
        onde XXXXXXXXXXXXX é um timestamp + contador sequencial para garantir unicidade.
        """
        import time
        from datetime import datetime
        
        ano_atual = datetime.now().year
        timestamp = int(time.time() * 1000000)  # timestamp em microsegundos
        
        # Conta quantas intercorrências já foram criadas no banco para adicionar um contador
        contador = Intercorrencia.objects.count() + 1
        
        # Gera o identificador único combinando timestamp e contador
        identificador = f"{timestamp}{contador:05d}"
        
        return f"GIPE-{ano_atual}/{identificador}"

    @property
    def pode_ser_editado_por_diretor(self):
        """Verifica se ainda pode ser editado pelo diretor"""
        return self.status == "em_preenchimento_diretor"

    @property
    def pode_ser_editado_por_dre(self):
        """Verifica se pode ser editado pela DRE"""
        return self.status in ["em_preenchimento_diretor", "em_preenchimento_assistente", "enviado_para_dre", "em_preenchimento_dre"]
    
    @property
    def pode_ser_editado_por_gipe(self):
        """Verifica se pode ser editado pela GIPE"""
        return self.status in ["em_preenchimento_diretor", "em_preenchimento_assistente", "em_preenchimento_dre", "em_preenchimento_gipe", "enviado_para_dre", "enviado_para_gipe"]