import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class AnexosService:
    """
    Service para comunicação com o microserviço de anexos
    """
    
    BASE_URL = getattr(settings, 'ANEXOS_API_URL', 'http://localhost:8002/api-anexos/v1')
    INTERNAL_TOKEN = getattr(settings, 'INTERNAL_SERVICE_TOKEN', None)
    TIMEOUT = 30  # 30 segundos (pode ter muitos anexos)
    
    @classmethod
    def deletar_anexos_intercorrencia(cls, intercorrencia_uuid: str) -> dict:
        """
        Solicita ao microserviço de anexos que delete todos os anexos
        de uma intercorrência.
        
        Args:
            intercorrencia_uuid: UUID da intercorrência
            
        Returns:
            dict com resultado da operação:
            {
                'success': bool,
                'data': dict (se sucesso),
                'error': str (se falha),
                'error_type': str (categoria do erro)
            }
        """
        url = f"{cls.BASE_URL}/anexos/deletar-por-intercorrencia/"
        
        headers = {
            'Content-Type': 'application/json',
            'X-Internal-Service-Token': cls.INTERNAL_TOKEN
        }
        
        payload = {
            'intercorrencia_uuid': str(intercorrencia_uuid)
        }
        
        try:
            logger.info(
                f"Solicitando exclusão de anexos da intercorrência: {intercorrencia_uuid} "
                f"no endpoint: {url}"
            )
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=cls.TIMEOUT
            )
            
            # Se o status não for 2xx, lançar exceção
            response.raise_for_status()
            
            data = response.json()
            
            anexos_deletados = data.get('total_anexos', 0)
            anexos_com_erro = data.get('anexos_com_erro', 0)
            
            logger.info(
                f"Anexos da intercorrência {intercorrencia_uuid} processados. "
                f"Deletados: {anexos_deletados}, Erros: {anexos_com_erro}"
            )
            
            return {
                'success': True,
                'data': data,
                'error': None,
                'error_type': None,
                'total_anexos': anexos_deletados
            }
        
        except requests.exceptions.Timeout:
            error_msg = (
                f"Timeout ao comunicar com o serviço de anexos. "
                f"O serviço demorou mais de {cls.TIMEOUT} segundos para responder."
            )
            logger.error(error_msg)
            
            return {
                'success': False,
                'data': None,
                'error': error_msg,
                'error_type': 'TIMEOUT'
            }
        
        except requests.exceptions.ConnectionError as e:
            error_msg = (
                f"Falha ao conectar com o serviço de anexos. "
                f"Verifique se o serviço está disponível em {cls.BASE_URL}"
            )
            logger.error(f"{error_msg} - Detalhes: {str(e)}")
            
            return {
                'success': False,
                'data': None,
                'error': error_msg,
                'error_type': 'CONNECTION_ERROR'
            }
        
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            
            try:
                error_data = e.response.json()
                error_detail = error_data.get('detail', str(e))
            except Exception.HTTPError:
                error_detail = str(e)
            
            error_msg = (
                f"Erro HTTP {status_code} ao deletar anexos. "
                f"Detalhes: {error_detail}"
            )
            logger.error(error_msg)
            
            return {
                'success': False,
                'data': None,
                'error': error_msg,
                'error_type': f'HTTP_{status_code}'
            }
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Erro na requisição ao serviço de anexos: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'data': None,
                'error': error_msg,
                'error_type': 'REQUEST_ERROR'
            }
        
        except Exception as e:
            error_msg = f"Erro inesperado ao comunicar com serviço de anexos: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'data': None,
                'error': error_msg,
                'error_type': 'UNEXPECTED_ERROR'
            }