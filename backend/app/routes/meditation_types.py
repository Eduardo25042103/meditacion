from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


from app.core.database import get_db
from app.models.models import MeditationType
from app.schemas.meditation_schemas import (
    MeditationTypeCreate, MeditationTypeUpdate, MeditationTypeOut
)
from app.utils.security import check_admin_role


router = APIRouter(prefix="/meditation-type", tags=["Meditation Types"])



@router.get("/", response_model=list[MeditationTypeOut])
async def list_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MeditationType))
    return result.scalars().all()


@router.post(
    "/",
    response_model=MeditationTypeOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_admin_role)]
)
async def create_type(
    type_in: MeditationTypeCreate,
    db: AsyncSession = Depends(get_db)
):
    new = MeditationType(**type_in.dict())
    db.add(new)
    await db.commit()
    await db.refresh(new)
    return new


@router.put(
    "/{type_id}",
    response_model=MeditationTypeOut,
    dependencies=[Depends(check_admin_role)]
)
async def update_type(
    type_id: int,
    type_in: MeditationTypeUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MeditationType).where(MeditationType.id == type_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Tipo no encontrado")
    for field,val in type_in.dict(exclude_unset=True).items():
        setattr(obj, field, val)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/{type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_admin_role)]
)
async def delete_type(
    type_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(MeditationType).where(MeditationType.id == type_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Tipo no encontrado")
    await db.delete(obj)
    await db.commit()