from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


from app.core.database import get_db
from app.models.models import UserPreferences
from app.schemas.preferences_schemas import PreferencesOut
from app.utils.security import get_current_user
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


@router.post("/generate", status_code=200)
async def generate_preferences(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    await update_user_preferences(current_user.id, db)
    return {"message": "Preferencias actualizadas exitosamente"}