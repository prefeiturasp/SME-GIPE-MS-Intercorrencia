from django.contrib import admin

from .models.declarante import Declarante
from .models.envolvido import Envolvido
from .models.intercorrencia import Intercorrencia
from .models.tipos_ocorrencia import TipoOcorrencia
from django import forms

from intercorrencias.choices.info_agressor_choices import (
    MotivoOcorrencia,
    GrupoEtnicoRacial,
    Genero,
    FrequenciaEscolar,
    EtapaEscolar,
)


class IntercorrenciaAdminForm(forms.ModelForm):
    # sobrescreve o campo do ModelForm
    motivacao_ocorrencia = forms.MultipleChoiceField(
        choices=MotivoOcorrencia.choices,
        widget=forms.CheckboxSelectMultiple,  # ou forms.SelectMultiple
        required=False,
        label="O que motivou a ocorrência?",
        help_text="Selecione uma ou mais motivações."
    )


@admin.register(Intercorrencia)
class IntercorrenciaAdmin(admin.ModelAdmin):
    form = IntercorrenciaAdminForm

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

    def get_tipos_ocorrencia(self, obj):
        """Mostra os tipos de ocorrência como texto no admin."""
        return ", ".join([t.nome for t in obj.tipos_ocorrencia.all()])

    get_tipos_ocorrencia.short_description = "Tipos de Ocorrência"

    def get_fieldsets(self, request, obj=None):
        base_fieldsets = (
            ('Seção inicial (Diretor)', {
                'fields': (
                    'status', 'user_username',
                    'data_ocorrencia', 'unidade_codigo_eol', 'dre_codigo_eol',
                    'sobre_furto_roubo_invasao_depredacao', "motivacao_ocorrencia",
                )
            }),
            ('Seção Final (Diretor)', {
                'fields': (
                    'declarante',
                    'comunicacao_seguranca_publica',
                    'protocolo_acionado',
                )
            }),
            ('Metadados', {
                'fields': ('uuid', 'criado_em', 'atualizado_em'),
                'classes': ('collapse',)
            }),
        )

        if obj and obj.sobre_furto_roubo_invasao_depredacao:
            extra_fieldsets = (
                ('Seção É Furto/Roubo (Diretor)', {
                    'fields': ('tipos_ocorrencia', 'descricao_ocorrencia', 'smart_sampa_situacao')
                }),
            )
        else:
            extra_fieldsets = (
                ('Seção Não Furto/Roubo (Diretor)', {
                    'fields': ('tipos_ocorrencia', 'descricao_ocorrencia', 'envolvido', 'tem_info_agressor_ou_vitima')
                }),
            )

        return base_fieldsets[:1] + extra_fieldsets + base_fieldsets[1:]


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

@admin.register(Envolvido)
class EnvolvidoAdmin(admin.ModelAdmin):
    list_display = ("perfil_dos_envolvidos", "ativo")
    search_fields = ("perfil_dos_envolvidos",)
    list_filter = ("ativo",)