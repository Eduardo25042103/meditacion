from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine


# Importar routers (los agregaremos luego)
from app.routes import auth, meditation_types, meditations, sessions, preferences
# from app.routes import auth, meditations, users, etc

app = FastAPI(
    title="API de Meditación",
    version="1.0.0",
    description="Backend con FastAPI para app de meditación 🧘‍♂️"
)

# CORS - para permitir acceso desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ en producción limitar esto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas base
@app.get("/")
def root():
    return {"message": "🧘‍♀️ Bienvenido a la API de meditación"}

# Para crear tablas para bd si no existen 
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Montar routers acá
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(meditation_types.router)
app.include_router(meditations.router)
app.include_router(sessions.router)
app.include_router(preferences.router)


