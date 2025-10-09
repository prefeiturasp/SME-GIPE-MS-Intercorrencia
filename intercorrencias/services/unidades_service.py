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
    
def validar_unidade_usuario(codigo_eol: str, token: str) -> dict | None:
    """
    Valida se a unidade informada pertence ao usuário autenticado.
    """

    logger.info("Validando se a unidade %s pertence ao usuário autenticado", codigo_eol)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    try:
        url = f"{BASE}/{codigo_eol}/verificar-unidade/"
        r = requests.get(url, headers=headers, timeout=3.0)

        if r.status_code in (200, 403):
            return r.json()
        
        return None

    except requests.RequestException as e:
        raise ExternalServiceError(f"Falha ao validar unidade: {e}") from e