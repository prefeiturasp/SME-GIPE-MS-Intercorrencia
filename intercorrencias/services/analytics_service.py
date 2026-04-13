import math
from datetime import datetime
from typing import Any

import polars as pl
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


class AnalyticsPresenter:

    def intercorrencias_por_dre(self, df: pl.DataFrame) -> list[dict]:

        if df.is_empty():
            return []
        
        resultado = (
            df.group_by("dre_codigo_eol")
            .agg([
                pl.len().alias("total"),
                (pl.col("sobre_furto_roubo_invasao_depredacao") == True).sum().alias("patrimonial"),
                (pl.col("sobre_furto_roubo_invasao_depredacao") == False).sum().alias("interpessoal"),
            ])
            .sort("total", descending=True)
        )

        return [
            {
                "codigo_eol": row["dre_codigo_eol"],
                "total": row["total"],
                "patrimonial": row["patrimonial"],
                "interpessoal": row["interpessoal"],
            }
            for row in resultado.iter_rows(named=True)
        ]
    
    def intercorrencias_por_status(self, df: pl.DataFrame) -> list[dict]:

        STATUS_MAP = dict(Intercorrencia.STATUS_CHOICES)

        base = {
            status: {"total": 0, "patrimonial": 0, "interpessoal": 0}
            for status in STATUS_MAP.keys()
        }

        if not df.is_empty():
            resultado = (
                df.group_by("status")
                .agg([
                    pl.len().alias("total"),
                    (pl.col("sobre_furto_roubo_invasao_depredacao") == True).sum().alias("patrimonial"),
                    (pl.col("sobre_furto_roubo_invasao_depredacao") == False).sum().alias("interpessoal"),
                ])
            )

            for row in resultado.iter_rows(named=True):
                base[row["status"]] = {
                    "total": row["total"],
                    "patrimonial": row["patrimonial"],
                    "interpessoal": row["interpessoal"],
                }

        return [
            {
                "status": STATUS_MAP.get(status, status),
                **valores
            }
            for status, valores in base.items()
        ]

    def cards_totalizadores(self, df: pl.DataFrame) -> list[dict]:

        if df.is_empty():
            return [
                {"total_intercorrencia": 0},
                {"intercorrencias_patrimoniais": 0},
                {"intercorrencias_interpessoais": 0},
                {"media_mensal": 0},
            ]
        
        resultado = df.select([
            pl.len().alias("total"),
            (pl.col("sobre_furto_roubo_invasao_depredacao") == True).sum().alias("patrimoniais"),
            (pl.col("sobre_furto_roubo_invasao_depredacao") == False).sum().alias("interpessoais"),
        ]).to_dicts()[0]

        total = resultado["total"]
        meses = df.select(pl.col("mes").unique()).shape[0] or 1

        return [
            {"total_intercorrencia": total},
            {"intercorrencias_patrimoniais": resultado["patrimoniais"]},
            {"intercorrencias_interpessoais": resultado["interpessoais"]},
            {"media_mensal": math.ceil(total / meses) if total else 0},
        ]


class AnalyticsService:

    def __init__(self):
        self.repository = IntercorrenciaRepository()
        self.transformer = AnalyticsTransformer()
        self.presenter = AnalyticsPresenter()

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

    def execute_pipeline_json(self, filtros: dict[str, Any]) -> dict[str, Any]:

        if not filtros:
            filtros = {
                "ano": [str(datetime.now().year)],
            }

        df = self.execute_pipeline(filtros)
        return {
            "intercorrencias_dre": self.presenter.intercorrencias_por_dre(df),
            "intercorrencias_status": self.presenter.intercorrencias_por_status(df),
            "cards": self.presenter.cards_totalizadores(df),
        }