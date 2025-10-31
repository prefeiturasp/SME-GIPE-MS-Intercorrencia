from django.contrib import admin

from .models.declarante import Declarante
from .models.intercorrencia import Intercorrencia
from .models.tipos_ocorrencia import TipoOcorrencia


@admin.register(Intercorrencia)
class IntercorrenciaAdmin(admin.ModelAdmin):
    list_display = (
        "user_username",
        "unidade_codigo_eol",
        "dre_codigo_eol",
        "sobre_furto_roubo_invasao_depredacao",
        "criado_em",
    )
    list_filter = ("user_username", "unidade_codigo_eol", "dre_codigo_eol", "sobre_furto_roubo_invasao_depredacao")
    search_fields = ("unidade_codigo_eol", "user_username", "dre_codigo_eol")
    readonly_fields = ("uuid", "criado_em", "atualizado_em")
    ordering = ("-criado_em",)
    fieldsets = (
        ('Seção inicial (Diretor)', {
            'fields': (
                'status', 'user_username',
                'data_ocorrencia', 'unidade_codigo_eol', 'dre_codigo_eol',
                'sobre_furto_roubo_invasao_depredacao'
            )
        }),
        ('Seção Furto/Roubo (Diretor)', {
            'fields': (
                'tipos_ocorrencia', 'descricao_ocorrencia', 'smart_sampa_situacao'    
            )
        }),
        ('Metadados', {
            'fields': ('uuid', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    def get_tipos_ocorrencia(self, obj):
        """Mostra os tipos de ocorrência como texto no admin."""
        return ", ".join([t.nome for t in obj.tipos_ocorrencia.all()])

    get_tipos_ocorrencia.short_description = "Tipos de Ocorrência"

@admin.register(TipoOcorrencia)
class TipoOcorrenciaAdmin(admin.ModelAdmin):
    list_display = ("nome", "ativo")
    search_fields = ("nome",)
    list_filter = ("ativo",)

@admin.register(Declarante)
class DeclaranteAdmin(admin.ModelAdmin):
    list_display = ("declarante", "ativo")
    search_fields = ("declarante",)
    list_filter = ("ativo",)