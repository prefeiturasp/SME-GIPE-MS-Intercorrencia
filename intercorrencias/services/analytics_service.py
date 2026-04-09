import polars as pl
from typing import Any

from django.db.models import OuterRef, Exists

from intercorrencias.models import Intercorrencia, PessoaAgressora


class IntercorrenciaRepository:

    def fetch(self, filtros: dict):
        
        queryset = Intercorrencia.objects.all()

        inter_filters = {
            "data_ocorrencia__year__in": filtros.get("ano"),
            "data_ocorrencia__month__in": filtros.get("mes"),
            "dre_codigo_eol__in": filtros.get("dre"),
            "unidade_codigo_eol__in": filtros.get("unidade"),
        }

        inter_filters = {k: v for k, v in inter_filters.items() if v}
        queryset = queryset.filter(**inter_filters)

        pessoa_filters = {
            "genero__in": filtros.get("genero"),
            "etapa_escolar__in": filtros.get("etapa_escolar"),
            "idade": filtros.get("idade"),
        }

        pessoa_filters = {k: v for k, v in pessoa_filters.items() if v}
        if pessoa_filters.get("idade"):
            pessoa_filters["idade_em_meses"] = filtros.get("idade_em_meses", False)

        if pessoa_filters:
            pessoa_qs = PessoaAgressora.objects.filter(
                intercorrencia=OuterRef('pk'),
                **pessoa_filters
            )

            queryset = queryset.annotate(
                has_matching_person=Exists(pessoa_qs)
            ).filter(has_matching_person=True)

        return queryset


class AnalyticsTransformer:

    def transform(self, df: pl.LazyFrame) -> pl.LazyFrame:
        return df.with_columns([
            pl.col("data_ocorrencia").dt.year().alias("ano"),
            pl.col("data_ocorrencia").dt.month().alias("mes"),
            pl.col("data_ocorrencia").dt.quarter().alias("periodo"),
        ])

    def apply_filters(self, df: pl.LazyFrame, filtros: dict[str, Any]) -> pl.LazyFrame:
        mapping = {"periodo": "periodo"}

        conditions = [
            pl.col(mapping[k]).is_in(v)
            for k, v in filtros.items()
            if k in mapping and v
        ]

        if conditions:
            df = df.filter(pl.all_horizontal(conditions))

        return df


class AnalyticsService:

    def __init__(self):
        self.repository = IntercorrenciaRepository()
        self.transformer = AnalyticsTransformer()

    def execute_pipeline(
        self,
        filtros: dict[str, Any]
    ) -> pl.DataFrame:

        queryset = self.repository.fetch(filtros)

        if not queryset.exists():
            return pl.DataFrame({
                "uuid": [],
                "data_ocorrencia": [],
                "dre_codigo_eol": [],
                "unidade_codigo_eol": [],
                "sobre_furto_roubo_invasao_depredacao": [],
                "motivacao_ocorrencia": [],
                "tipos_ocorrencia": [],
                "status": [],
            })

        lista_valores = []
        for obj in queryset.prefetch_related("tipos_ocorrencia"):
            lista_valores.append({
                "uuid": obj.uuid,
                "data_ocorrencia": obj.data_ocorrencia,
                "dre_codigo_eol": obj.dre_codigo_eol,
                "unidade_codigo_eol": obj.unidade_codigo_eol,
                "sobre_furto_roubo_invasao_depredacao": obj.sobre_furto_roubo_invasao_depredacao,
                "motivacao_ocorrencia": obj.motivacao_ocorrencia,
                "tipos_ocorrencia": [t.nome for t in obj.tipos_ocorrencia.all()],
                "status": obj.status,
            })

        df_lazy = pl.LazyFrame(lista_valores)

        df_lazy = self.transformer.transform(df_lazy)
        df_lazy = self.transformer.apply_filters(df_lazy, filtros)

        df = df_lazy.collect()

        return df