import pytest
import polars as pl
from datetime import datetime

from django.utils import timezone

from intercorrencias.models import Intercorrencia, PessoaAgressora
from intercorrencias.services.analytics_service import (
    IntercorrenciaRepository,
    AnalyticsTransformer,
    AnalyticsService,
    AnalyticsPresenter,
)


@pytest.mark.django_db
class TestAnalyticsPipeline:

    def _create_intercorrencia(self, date, dre=1, unidade=10, status="ativo"):
        return Intercorrencia.objects.create(
            data_ocorrencia=timezone.make_aware(date),
            dre_codigo_eol=dre,
            unidade_codigo_eol=unidade,
            status=status,
        )

    def test_fetch_sem_filtros(self):
        self._create_intercorrencia(datetime(2024, 1, 1))

        repo = IntercorrenciaRepository()
        result = repo.fetch({})

        assert result.count() == 1

    def test_fetch_filtro_ano(self):
        self._create_intercorrencia(datetime(2026, 1, 1))

        repo = IntercorrenciaRepository()
        result = repo.fetch({"ano": [2026]})

        assert result.count() == 1

    def test_fetch_filtro_mes(self):
        self._create_intercorrencia(datetime(2026, 3, 1))

        repo = IntercorrenciaRepository()
        result = repo.fetch({"mes": [3]})

        assert result.count() == 1

    def test_fetch_filtro_dre(self):
        self._create_intercorrencia(datetime(2026, 1, 1), dre=108300)

        repo = IntercorrenciaRepository()
        result = repo.fetch({"dre": [108300]})

        assert result.count() == 1

    def test_fetch_filtro_unidade(self):
        self._create_intercorrencia(datetime(2026, 1, 1), unidade=123456)

        repo = IntercorrenciaRepository()
        result = repo.fetch({"unidade": [123456]})

        assert result.count() == 1

    def test_fetch_filtro_genero(self):
        inter = self._create_intercorrencia(datetime(2026, 1, 1))

        PessoaAgressora.objects.create(
            intercorrencia=inter,
            genero="masculino",
            etapa_escolar="FUNDAMENTAL",
            idade=10,
            idade_em_meses=False,
        )

        repo = IntercorrenciaRepository()
        result = repo.fetch({"genero": ["masculino"]})

        assert result.count() == 1

    def test_fetch_filtro_etapa_escolar(self):
        inter = self._create_intercorrencia(datetime(2026, 1, 1))

        PessoaAgressora.objects.create(
            intercorrencia=inter,
            genero="feminino",
            etapa_escolar="FUNDAMENTAL",
            idade=10,
            idade_em_meses=False,
        )

        repo = IntercorrenciaRepository()
        result = repo.fetch({"etapa_escolar": ["FUNDAMENTAL"]})

        assert result.count() == 1

    def test_fetch_filtro_idade(self):
        inter = self._create_intercorrencia(datetime(2026, 1, 1))

        PessoaAgressora.objects.create(
            intercorrencia=inter,
            genero="feminino",
            etapa_escolar="FUNDAMENTAL",
            idade=6,
            idade_em_meses=False,
        )

        repo = IntercorrenciaRepository()
        result = repo.fetch({"idade": 6})

        assert result.count() == 1

    def test_fetch_com_idade_em_meses(self):
        inter = self._create_intercorrencia(datetime(2026, 1, 1))

        PessoaAgressora.objects.create(
            intercorrencia=inter,
            genero="feminino",
            etapa_escolar="INFANTIL",
            idade=6,
            idade_em_meses=True,
        )

        repo = IntercorrenciaRepository()

        filtros = {
            "idade": 6,
            "idade_em_meses": True,
        }

        result = repo.fetch(filtros)

        assert result.count() == 1

    def test_transform_adiciona_colunas(self):
        df = pl.LazyFrame([
            {"data_ocorrencia": "2024-03-15"}
        ]).with_columns(
            pl.col("data_ocorrencia").str.strptime(pl.Date)
        )

        transformer = AnalyticsTransformer()
        result = transformer.transform(df).collect()

        assert "ano" in result.columns
        assert "mes" in result.columns
        assert "periodo" in result.columns

    def test_apply_filters_periodo(self):
        df = pl.LazyFrame([
            {"periodo": 1},
            {"periodo": 2},
        ])

        transformer = AnalyticsTransformer()
        filtros = {"periodo": [1]}

        result = transformer.apply_filters(df, filtros).collect()

        assert len(result) == 1
        assert result["periodo"][0] == 1

    def test_apply_filters_periodo_multiplo(self):
        df = pl.LazyFrame([
            {"periodo": 1},
            {"periodo": 2},
            {"periodo": 3},
        ])

        transformer = AnalyticsTransformer()
        filtros = {"periodo": [1, 2]}

        result = transformer.apply_filters(df, filtros).collect()

        assert len(result) == 2

    def test_execute_pipeline_retorna_dataframe(self):
        self._create_intercorrencia(datetime(2024, 1, 1))

        service = AnalyticsService()
        df = service.execute_pipeline({})

        assert df.shape[0] == 1
        assert "ano" in df.columns

    def test_execute_pipeline_vazio(self):
        service = AnalyticsService()

        df = service.execute_pipeline({})

        assert df.is_empty()

    def test_cards_totalizadores_com_dados(self):
        df = pl.DataFrame([
            {"mes": 1, "sobre_furto_roubo_invasao_depredacao": True},
            {"mes": 1, "sobre_furto_roubo_invasao_depredacao": False},
            {"mes": 2, "sobre_furto_roubo_invasao_depredacao": True},
        ])

        presenter = AnalyticsPresenter()
        result = presenter.cards_totalizadores(df)

        assert result[0]["total_intercorrencia"] == 3
        assert result[1]["intercorrencias_patrimoniais"] == 2
        assert result[2]["intercorrencias_interpessoais"] == 1
        assert result[3]["media_mensal"] == 2  # ceil(3/2)

    def test_cards_totalizadores_vazio(self):
        df = pl.DataFrame([])

        presenter = AnalyticsPresenter()
        result = presenter.cards_totalizadores(df)

        assert result == [
            {"total_intercorrencia": 0},
            {"intercorrencias_patrimoniais": 0},
            {"intercorrencias_interpessoais": 0},
            {"media_mensal": 0},
        ]

    def test_execute_pipeline_json_com_dados(self):

        self._create_intercorrencia(datetime(2024, 1, 1))

        service = AnalyticsService()

        result = service.execute_pipeline_json({})

        assert "cards" in result
        assert isinstance(result["cards"], list)

    def test_execute_pipeline_json_sem_dados(self):
        service = AnalyticsService()

        result = service.execute_pipeline_json({})

        assert result["cards"] == [
            {"total_intercorrencia": 0},
            {"intercorrencias_patrimoniais": 0},
            {"intercorrencias_interpessoais": 0},
            {"media_mensal": 0},
        ]

    def test_execute_pipeline_json_filtros_none(self):
        
        self._create_intercorrencia(datetime.now())

        service = AnalyticsService()
        result = service.execute_pipeline_json({})

        assert "cards" in result
    
    def test_intercorrencias_por_dre_vazio(self):
        df = pl.DataFrame([])

        presenter = AnalyticsPresenter()
        result = presenter.intercorrencias_por_dre(df)

        assert result == []
    
    def test_intercorrencias_por_dre_simples(self):
        df = pl.DataFrame([
            {
                "dre_codigo_eol": 100,
                "sobre_furto_roubo_invasao_depredacao": True
            },
            {
                "dre_codigo_eol": 100,
                "sobre_furto_roubo_invasao_depredacao": False
            },
        ])

        presenter = AnalyticsPresenter()
        result = presenter.intercorrencias_por_dre(df)

        assert result == [
            {
                "codigo_eol": 100,
                "total": 2,
                "patrimonial": 1,
                "interpessoal": 1,
            }
        ]
    
    def test_intercorrencias_por_dre_multiplos(self):
        df = pl.DataFrame([
            {"dre_codigo_eol": 100, "sobre_furto_roubo_invasao_depredacao": True},
            {"dre_codigo_eol": 100, "sobre_furto_roubo_invasao_depredacao": False},
            {"dre_codigo_eol": 200, "sobre_furto_roubo_invasao_depredacao": True},
        ])

        presenter = AnalyticsPresenter()
        result = presenter.intercorrencias_por_dre(df)

        assert len(result) == 2

        assert result[0]["codigo_eol"] == 100
        assert result[0]["total"] == 2

        assert result[1]["codigo_eol"] == 200
        assert result[1]["total"] == 1
    
    def test_intercorrencias_por_dre_contadores(self):
        df = pl.DataFrame([
            {"dre_codigo_eol": 300, "sobre_furto_roubo_invasao_depredacao": True},
            {"dre_codigo_eol": 300, "sobre_furto_roubo_invasao_depredacao": True},
            {"dre_codigo_eol": 300, "sobre_furto_roubo_invasao_depredacao": False},
        ])

        presenter = AnalyticsPresenter()
        result = presenter.intercorrencias_por_dre(df)

        assert result[0]["total"] == 3
        assert result[0]["patrimonial"] == 2
        assert result[0]["interpessoal"] == 1
    
    def test_intercorrencias_por_dre_ordenacao(self):
        df = pl.DataFrame([
            {"dre_codigo_eol": 1, "sobre_furto_roubo_invasao_depredacao": True},
            {"dre_codigo_eol": 2, "sobre_furto_roubo_invasao_depredacao": True},
            {"dre_codigo_eol": 2, "sobre_furto_roubo_invasao_depredacao": False},
        ])

        presenter = AnalyticsPresenter()
        result = presenter.intercorrencias_por_dre(df)

        assert result[0]["codigo_eol"] == 2
        assert result[1]["codigo_eol"] == 1