from fastapi.security import HTTPBasic, APIKeyHeader


BasicAuth = HTTPBasic()

HeaderKey = APIKeyHeader(name="x-key")

