import requests
import logging
from django.conf import settings
from requests.exceptions import RequestException, Timeout, HTTPError

logger = logging.getLogger(__name__)


class IntercorrenciasService:
    """
    Service para comunicação com o microserviço do GIPE
    """

    BASE_URL = settings.USERS_BASE_URL
    INTERNAL_TOKEN = getattr(settings, "INTERNAL_SERVICE_TOKEN", None)
    TIMEOUT = 30

    @classmethod
    def alerta_finalizacao_intercorrencia(cls, username: str, data_ocorrencia: str, uuid_ocorrencia: str) -> dict:
        url = f"{cls.BASE_URL}/intercorrencias/alerta-finalizacao-ocorrencia/"

        headers = {
            "Content-Type": "application/json",
            "X-Internal-Service-Token": cls.INTERNAL_TOKEN,
        }

        payload = {
            "data_ocorrencia": data_ocorrencia,
            "username": username,
            "uuid_ocorrencia": uuid_ocorrencia,
        }

        logger.info(
            "Iniciando requisição para envio de e-mail interno",
            extra={
                "url": url,
                "username": username,
                "uuid_ocorrencia": uuid_ocorrencia,
            },
        )

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=cls.TIMEOUT,
            )

            response.raise_for_status()

            data = response.json()

            logger.info(
                "Requisição concluída com sucesso",
                extra={
                    "status_code": response.status_code,
                    "username": username,
                    "data_ocorrencia": data_ocorrencia,
                    "uuid_ocorrencia": uuid_ocorrencia,
                },
            )

            return data

        except Timeout:
            logger.error(
                "Timeout ao chamar serviço de e-mail",
                extra={
                    "url": url,
                    "username": username,
                    "timeout": cls.TIMEOUT,
                },
            )
            return {"success": False, "error": "timeout"}

        except HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else None
            response_text = http_err.response.text if http_err.response else None

            logger.error(
                "Erro HTTP ao chamar serviço de e-mail",
                extra={
                    "url": url,
                    "username": username,
                    "status_code": status_code,
                    "response": response_text,
                },
            )

            return {
                "success": False,
                "error": "http_error",
                "status_code": status_code,
            }

        except RequestException as req_err:
            logger.error(
                "Erro de conexão ao chamar serviço de e-mail",
                extra={
                    "url": url,
                    "username": username,
                    "error": str(req_err),
                },
            )

            return {"success": False, "error": "connection_error"}

        except Exception:
            logger.exception(
                "Erro inesperado ao chamar serviço de e-mail",
                extra={
                    "url": url,
                    "username": username,
                },
            )

            return {"success": False, "error": "unexpected_error"}