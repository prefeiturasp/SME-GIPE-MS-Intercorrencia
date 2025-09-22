import time
import requests
import jwt
from dataclasses import dataclass
from django.conf import settings
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
import logging
logger = logging.getLogger(__name__)

VERIFY_URL = settings.AUTH_VERIFY_URL

@dataclass
class ExternalUser:
    username: str
    name: str | None = None
    cargo_codigo: int | None = None
    is_authenticated: bool = True

class RemoteJWTAuthentication(BaseAuthentication):
    """
    Verifica o JWT chamando o serviço de Auth.
    Decodifica o payload (sem verificar assinatura) *após* a verificação.
    Faz cache curto para reduzir latência.
    """

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        
        if not auth or auth[0].lower() != b"bearer" or len(auth) != 2:
            return None  # sem credenciais -> DRF tratará como não autenticado

        token = auth[1].decode("utf-8")
        user_payload = self._verify_and_get_payload(token)  # dict

        logger.info("Payload do usuário: %s", user_payload)

        username = (
            user_payload.get("username")
            or user_payload.get("sub")
            or user_payload.get("user_id")
        )
        if not username:
            raise AuthenticationFailed("Token sem 'username' ou 'sub'.")

        user = ExternalUser(
            username=username,
            name=user_payload.get("name"),
            cargo_codigo=user_payload.get("perfil_codigo") or user_payload.get("cargo_codigo"),
        )
        return (user, None)

    def _verify_and_get_payload(self, token: str) -> dict:

        logger.info("Verificando token no serviço A: %s", settings.AUTH_VERIFY_URL)

        cache_key = f"jwtv:{hash(token)}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 1) Verifica no serviço A
        try:
            logger.info(f"Enviando requisição para o serviço A... {VERIFY_URL}")
            r = requests.post(VERIFY_URL, json={"token": token}, timeout=3.0)
            logger.info("Resposta do serviço A: %s", r.status_code)
        except requests.RequestException as e:   # ✅ classe base de todas as exceções de rede do requests
            raise AuthenticationFailed(f"Falha ao contatar serviço de autenticação: {e}")
                
        if r.status_code != 200:
            raise AuthenticationFailed("Token inválido ou expirado.")

        
        try:
            # Use the secret or public key from settings to verify the signature
            payload = jwt.decode(
                token,
                key=settings.AUTH_PUBLIC_KEY if hasattr(settings, "AUTH_PUBLIC_KEY") else settings.SECRET_KEY,
                algorithms=["HS256", "RS256"],  # Adjust algorithms as needed
                options={"verify_signature": True}
            )
        except jwt.PyJWTError:
            raise AuthenticationFailed("Token malformado.")

        # TTL do cache: respeite o exp do token, com teto curto
        now = int(time.time())
        exp = int(payload.get("exp", now + 60))
        ttl = max(1, min(60, exp - now))  # até 60s
        cache.set(cache_key, payload, ttl)
        return payload
