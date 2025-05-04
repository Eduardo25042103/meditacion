from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.models.models import User
from app.schemas.auth_schemas import UserCreate
from app.utils.security import hash_password

from datetime import datetime


router = APIRouter()


@router.post("/register", status_code=201)
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