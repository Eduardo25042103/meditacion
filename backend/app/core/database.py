import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

#Configuración bd
DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)

#Motor async
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    poolclass=NullPool,
)

#Sesion async
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()

#Dependency para FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        
        finally:
            await session.close()

