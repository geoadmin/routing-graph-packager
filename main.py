from arq import create_pool
from arq.connections import RedisSettings
from sqlmodel import SQLModel

from routing_packager_app import create_app
from routing_packager_app.config import SETTINGS

app = create_app()


@app.on_event("startup")
async def startup_event():
    SQLModel.metadata.create_all(checkfirst=True)
    app.state.redis_pool = await create_pool(RedisSettings(SETTINGS.REDIS_URL))
