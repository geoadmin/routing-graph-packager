import uvicorn as uvicorn
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from sqlmodel import SQLModel

from routing_packager_app import create_app
from routing_packager_app.db import engine
from routing_packager_app.config import SETTINGS
from routing_packager_app.utils.db_utils import add_admin_user

app: FastAPI = create_app()


@app.on_event("startup")
async def startup_event():
    SQLModel.metadata.create_all(engine, checkfirst=True)
    app.state.redis_pool = await create_pool(RedisSettings.from_dsn(SETTINGS.REDIS_URL))
    add_admin_user()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
