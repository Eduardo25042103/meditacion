from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# Importar routers (los agregaremos luego)
from app.routes import auth
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

# Montar routers acá
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
# app.include_router(meditations.router, prefix="/meditations")


