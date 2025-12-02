import pytest
from intercorrencias.choices.gipe_choices import (
    EnvolveArmaOuAtaque,
    AmeacaFoiRealizadaDeQualManeira,
    CicloAprendizagem,
    get_values_gipe_choices,
)
from intercorrencias.choices.info_agressor_choices import MotivoOcorrencia


@pytest.mark.parametrize(
    "enum_class",
    [EnvolveArmaOuAtaque, AmeacaFoiRealizadaDeQualManeira, CicloAprendizagem, MotivoOcorrencia],
)
def test_enum_values_and_labels(enum_class):
    for item in enum_class:
        assert isinstance(item.value, str)
        assert isinstance(item.label, str)
        assert len(item.value) > 0
        assert len(item.label) > 0

def test_get_values_gipe_choices_returns_expected_keys():
    result = get_values_gipe_choices()

    expected_keys = {
        "envolve_arma_ou_ataque",
        "ameaca_foi_realizada_de_qual_maneira",
        "motivo_ocorrencia",
        "ciclo_aprendizagem",
    }

    assert set(result.keys()) == expected_keys

def test_get_values_gipe_choices_values_have_correct_structure():
    result = get_values_gipe_choices()

    for key, values in result.items():
        assert isinstance(values, list)
        assert len(values) > 0
        for item in values:
            assert isinstance(item, dict)
            assert "value" in item
            assert "label" in item
            assert isinstance(item["value"], str)
            assert isinstance(item["label"], str)

def test_to_snake_case_inside_get_values_gipe_choices():
    result = get_values_gipe_choices()

    assert "envolve_arma_ou_ataque" in result
    assert "ameaca_foi_realizada_de_qual_maneira" in result
    assert "motivo_ocorrencia" in result
    assert "ciclo_aprendizagem" in result