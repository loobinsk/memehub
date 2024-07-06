import asyncio
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.database import get_db, Base
from app.main import app
from dotenv import load_dotenv
import os
from sqlalchemy.orm import declarative_base


load_dotenv()

DATABASE_TEST_URL = os.getenv('DATABASE_TEST_URL')

# Проверяем, что URL базы данных не пустой
if not DATABASE_TEST_URL:
    raise ValueError("DATABASE_TEST_URL не установлен или пуст")

engine_test = create_async_engine(DATABASE_TEST_URL, poolclass=NullPool)
async_session_maker = sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)

# Переопределяем зависимость для тестов
async def override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

app.dependency_overrides[get_db] = override_get_async_session

@pytest.fixture(autouse=True, scope='session')
async def prepare_database():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print('Удалены все таблицы')

# Создание event loop для тестов
@pytest.fixture(scope='session')
def event_loop(request):
    """Создает экземпляр event loop для каждого тестового случая."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session