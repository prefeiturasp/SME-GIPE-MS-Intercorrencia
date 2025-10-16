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
        "status",
        "get_tipos_ocorrencia",
        "descricao_ocorrencia",
        "smart_sampa_situacao",
        "criado_em",
    )
    list_filter = ("sobre_furto_roubo_invasao_depredacao", "dre_codigo_eol")
    search_fields = ("unidade_codigo_eol", "user_username", "dre_codigo_eol")
    readonly_fields = ("uuid", "criado_em", "atualizado_em")
    ordering = ("-criado_em",)

    def get_tipos_ocorrencia(self, obj):
        """Mostra os tipos de ocorrência como texto no admin."""
        return ", ".join([t.nome for t in obj.tipos_ocorrencia.all()])

    get_tipos_ocorrencia.short_description = "Tipos de Ocorrência"

@admin.register(TipoOcorrencia)
class TipoOcorrenciaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    search_fields = ("nome",)
    list_filter = ("ativo",)