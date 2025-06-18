from fastapi.security import HTTPBasic, APIKeyHeader
import hmac
import hashlib

from routing_packager_app.config import SETTINGS


BasicAuth = HTTPBasic(auto_error=False)

HeaderKey = APIKeyHeader(name="x-api-key", auto_error=False)


def hmac_hash(key: str) -> str:
    """Hash an API Key"""
    return hmac.new(SETTINGS.SECRET_KEY.encode(), key.encode(), hashlib.sha256).hexdigest()
