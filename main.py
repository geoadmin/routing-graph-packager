import uvicorn as uvicorn
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from pathlib import Path
from sqlmodel import SQLModel

from routing_packager_app import create_app
from routing_packager_app.db import engine, get_db
from routing_packager_app.config import SETTINGS
from routing_packager_app.api_v1.models import User

app: FastAPI = create_app()


@app.on_event("startup")
async def startup_event():
    SQLModel.metadata.create_all(engine, checkfirst=True)
    app.state.redis_pool = await create_pool(RedisSettings.from_dsn(SETTINGS.REDIS_URL))
    User.add_admin_user(next(get_db()))

    # create the valhalla directories
    for p in (SETTINGS.VALHALLA_DIR_8002, SETTINGS.VALHALLA_DIR_8003):
        p = Path(p)
        p.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
