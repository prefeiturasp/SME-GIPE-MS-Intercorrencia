import pytest
from intercorrencias.choices.info_agressor_choices import (
    MotivoOcorrencia,
    GrupoEtnicoRacial,
    Genero,
    FrequenciaEscolar,
    EtapaEscolar,
    get_values_info_agressor_choices
)

def test_motivo_ocorrencia_values():
    expected_values = {
        "bullying",
        "cyberbullying",
        "atividades_ilicitas",
        "homofobia",
        "ideologias_extremistas",
        "misoginia_machismo",
        "racismo",
        "violencia_genero",
        "capacitismo",
        "relacoes_afetivas",
        "uso_drogas",
        "vinganca",
        "xenofobia",
        "outros",
    }
    assert set(MotivoOcorrencia.values) == expected_values


@pytest.mark.parametrize(
    "enum_class",
    [GrupoEtnicoRacial, Genero, FrequenciaEscolar, EtapaEscolar],
)

def test_enum_has_values_and_labels(enum_class):
    for item in enum_class:
        assert isinstance(item.value, str)
        assert isinstance(item.label, str)
        assert len(item.value) > 0
        assert len(item.label) > 0

def test_get_values_info_agressor_choices_returns_expected_keys():
    result = get_values_info_agressor_choices()
    expected_keys = {
        "motivo_ocorrencia",
        "grupo_etnico_racial",
        "genero",
        "frequencia_escolar",
        "etapa_escolar",
    }
    assert set(result.keys()) == expected_keys


def test_get_values_info_agressor_choices_values_are_dicts_with_value_and_label():
    result = get_values_info_agressor_choices()
    for key, values in result.items():
        assert isinstance(values, list)
        assert len(values) > 0
        for item in values:
            assert isinstance(item, dict)
            assert "value" in item
            assert "label" in item
            assert isinstance(item["value"], str)
            assert isinstance(item["label"], str)