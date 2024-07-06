from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import database, init_db
from app.routers import router
from app.config import setup_logging
from contextlib import asynccontextmanager


logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await database.disconnect()

app = FastAPI(lifespan=lifespan)
#корсы для открытого обращения к нашему апи с стороны клиента
app.add_middleware(
    CORSMiddleware,
    allow_origins='*',
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)