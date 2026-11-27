from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from app.config import get_settings

settings = get_settings()

api_key_scheme = APIKeyHeader(
    name="X-API-Key",
    description="API-ключ для доступа к сервису",
)


async def get_api_key(
    api_key: Annotated[str, Depends(api_key_scheme)],
):
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return api_key
