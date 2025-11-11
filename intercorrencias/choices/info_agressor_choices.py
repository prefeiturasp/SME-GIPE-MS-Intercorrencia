import logging
from django.db import models

logger = logging.getLogger(__name__)

class MotivoOcorrencia(models.TextChoices):
    BULLYING = "bullying", "Bullying"
    CYBERBULLYING = "cyberbullying", "Cyberbullying"
    ATIVIDADES_ILICITAS = "atividades_ilicitas", "Envolvimento com atividades ilícitas"
    HOMOFOBIA = "homofobia", "Homofobia"
    IDEOLOGIAS_EXTREMISTAS = "ideologias_extremistas", "Ideologias extremistas (facista, nazista, discurso de ódio)"
    MISOGINIA_MACHISMO = "misoginia_machismo", "Misoginia/machismo"
    RACISMO = "racismo", "Racismo"
    VIOLENCIA_GENERO = "violencia_genero", "Violência de Gênero"
    CAPACITISMO = "capacitismo", "Capacitismo"
    RELACOES_AFETIVAS = "relacoes_afetivas", "Relações afetivas"
    USO_DROGAS = "uso_drogas", "Uso de drogas"
    VINGANCA = "vinganca", "Vingança"
    XENOFOBIA = "xenofobia", "Xenofobia"
    OUTROS = "outros", "Outros"


class GrupoEtnicoRacial(models.TextChoices):
    AMARELO = "amarelo", "Amarelo"
    BRANCO = "branco", "Branco"
    INDIGENA = "indigena", "Indígena"
    PRETO = "preto", "Preto"
    PARDO = "pardo", "Pardo"


class Genero(models.TextChoices):
    MULHER_TRANS = "mulher_trans", "Mulher trans"
    HOMEM_TRANS = "homem_trans", "Homem trans"
    MULHER_CIS = "mulher_cis", "Mulher cisgênero"
    HOMEM_CIS = "homem_cis", "Homem cisgênero"
    PESSOA_NAO_BINARIA = "pessoa_nao_binaria", "Pessoa não binária"


class FrequenciaEscolar(models.TextChoices):
    REGULARIZADA = "regularizada", "Regularizada"
    INFERIOR_75 = "inferior_75", "Inferior a 75%"
    INFERIOR_50 = "inferior_50", "Inferior a 50%"
    SEM_FREQUENCIA = "sem_frequencia", "Sem frequência"
    TRANSFERIDO_DRE = "transferido_dre", "Transferido para outra DRE"
    TRANSFERIDO_ESTADUAL = "transferido_estadual", "Transferido para a rede estadual"
    TRANSFERIDO_PARTICULAR = "transferido_particular", "Transferido para rede particular"
    NAO_SE_APLICA = "nao_se_aplica", "Não se aplica"


class EtapaEscolar(models.TextChoices):
    EDU_INFANTIL_CEI = "edu_infantil_cei", "Educação infantil - CEI"
    EDU_INFANTIL_EMEI = "edu_infantil_emei", "Educação Infantil - EMEI"
    FUNDAMENTAL_ALFABETIZACAO = "fundamental_alfabetizacao", "Ensino fundamental - Ciclo de alfabetização"
    FUNDAMENTAL_AUTORAL = "fundamental_autoral", "Ensino fundamental - Ciclo Autoral"
    ENSINO_MEDIO = "ensino_medio", "Ensino médio"
    NAO_SE_APLICA = "nao_se_aplica", "Não se aplica"


def get_values_info_agressor_choices():
    logger.info("Buscando info_agressor_choices...")
    choices_classes = [
        MotivoOcorrencia,
        GrupoEtnicoRacial,
        Genero,
        FrequenciaEscolar,
        EtapaEscolar
    ]
    return {
        cls.__name__.lower(): [c.label for c in cls] for cls in choices_classes
    }