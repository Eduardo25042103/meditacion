from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import get_db
from app.models.models import User
from app.schemas.auth_schemas import UserCreate, UserLogin, UserResponse, Token
from app.utils.security import hash_password, verify_password, create_access_token, get_current_active_user, get_current_user

from datetime import datetime


router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    #Verificar si usuario existe
    result = await db.execute(select(User).where(User.email == user.email))
    existing_user = result.scalars().first()
  

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario ya está registrado"
        )
    

    #Crear nuevo usuario
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        created_at=datetime.utcnow()
    )


    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)


    return {"message": "Usuario registrado correctamente ✅", "user_id": new_user.id} #De prueba actualmente xd


@router.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # Buscar usuario
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    # Validar credenciales
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"}
        )
    #Crear token JWT
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


# También puedes mantener el endpoint original para compatibilidad con el frontend
@router.post("/login-json", response_model=Token)
async def login_user_json(form_data: UserLogin, db: AsyncSession = Depends(get_db)):
    # Buscar usuario
    result = await db.execute(select(User).where(User.email == form_data.email))
    user = result.scalars().first()
    # Validar credenciales
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"}
        )
    #Crear token JWT
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_user_info(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("/protected-resource")
async def get_protected_resource(current_user: User = Depends(get_current_user)):
    return {
        "message": "Acceso autorizado",
        "user_id": current_user.id,
        "email": current_user.email
    }