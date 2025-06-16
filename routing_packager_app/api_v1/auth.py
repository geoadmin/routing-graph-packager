from fastapi.security import HTTPBasic, APIKeyHeader
from bcrypt import gensalt, hashpw, checkpw


BasicAuth = HTTPBasic()

HeaderKey = APIKeyHeader(name="x-key")


def hash_key(raw_key: str) -> str:
    return hashpw(raw_key.encode(), gensalt()).decode()


def check_key(raw_key: str, stored_key: str) -> bool:
    return checkpw(raw_key.encode(), stored_key.encode())
