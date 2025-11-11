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
        "motivoocorrencia",
        "grupoetnicoracial",
        "genero",
        "frequenciaescolar",
        "etapaescolar",
    }
    assert set(result.keys()) == expected_keys

def test_get_values_info_agressor_choices_values_are_lists():
    result = get_values_info_agressor_choices()
    for key, values in result.items():
        assert isinstance(values, list)
        assert all(isinstance(v, str) for v in values)
        assert len(values) > 0