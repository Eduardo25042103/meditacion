from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.models import UserPreferences
from app.schemas.preferences_schemas import PreferencesAllOut, PreferencesOut
from app.utils.security import get_current_user, check_admin_role
from app.services.preferences_service import update_user_preferences


router = APIRouter(prefix="/preferences", tags=["Preferences"])


@router.get("/", response_model=PreferencesOut)
async def get_preferences(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    res = await db.execute(
        select(UserPreferences)
        .where(UserPreferences.user_id == current_user.id)
    )
    prefs = res.scalar_one_or_none()
    if not prefs:
        raise HTTPException(status_code=404, detail="No se encontraron preferencias")
    return prefs


@router.get("/all", response_model=list[PreferencesAllOut])
async def get_all_preferences(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(check_admin_role)  # Solo para admins
):
    """Endpoint para que los admins vean todas las preferencias de usuarios"""
    res = await db.execute(
        select(UserPreferences)
        .options(selectinload(UserPreferences.user))  # Cargar info del usuario
    )
    all_preferences = res.scalars().all()
    return all_preferences


@router.post("/generate", status_code=200)
async def generate_preferences(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    await update_user_preferences(current_user.id, db)
    return {"message": "Preferencias actualizadas exitosamente"}