from django.contrib import admin

from .models.intercorrencia import Intercorrencia
from .models.tipos_ocorrencia import TipoOcorrencia


@admin.register(Intercorrencia)
class IntercorrenciaAdmin(admin.ModelAdmin):
    list_display = (
        "unidade_codigo_eol",
        "data_ocorrencia",
        "user_username",
        "dre_codigo_eol",
        "sobre_furto_roubo_invasao_depredacao",
        "criado_em",
    )
    list_filter = ("sobre_furto_roubo_invasao_depredacao", "dre_codigo_eol")
    search_fields = ("unidade_codigo_eol", "user_username", "dre_codigo_eol")
    readonly_fields = ("uuid", "criado_em", "atualizado_em")
    ordering = ("-criado_em",)


@admin.register(TipoOcorrencia)
class TipoOcorrenciaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    search_fields = ("nome",)
    list_filter = ("ativo",)