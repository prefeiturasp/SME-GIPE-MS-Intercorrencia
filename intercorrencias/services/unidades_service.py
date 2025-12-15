from django.conf import settings
import requests
import logging
logger = logging.getLogger(__name__)

class ExternalServiceError(Exception): ...

BASE = settings.UNIDADES_BASE_URL.rstrip("/")

def get_unidade(codigo_eol: str) -> dict | None:

    logger.info("Consultando unidade no serviço B: %s/%s", BASE, codigo_eol)

    try:
        url = f"{BASE}/{codigo_eol}/"
        r = requests.get(url, timeout=3.0)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise ExternalServiceError(f"Falha ao consultar unidade: {e}") from e


def get_unidades_em_lote(codigos_eol: set[str]) -> dict[str, dict]:

    if not codigos_eol:
        return {}

    logger.info("Consultando unidades em lote (%d registros).", len(codigos_eol))

    try:
        url = f"{BASE}/batch/"
        r = requests.post(
            url,
            json={"codigos": list(codigos_eol)},
            timeout=5.0,
        )
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise ExternalServiceError(f"Falha ao consultar unidades em lote: {e}") from e