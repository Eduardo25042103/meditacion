from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


from app.core.database import get_db
from app.models.models import Meditation, MeditationType
from app.schemas.meditation_schemas import MeditationCreate, MeditationUpdate, MeditationOut
from app.utils.security import check_admin_role


router = APIRouter(prefix="/meditations", tags=["Meditations"])



@router.get("/", response_model=list[MeditationOut])
async def list_meditations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Meditation).options(
            # Eager load the type relationship
            selectinload(Meditation.meditation_type)
        )
    )
    return result.scalars().all()



@router.post(
    "/",
    response_model=MeditationOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_admin_role)]
)
async def create_meditation(
    med_in: MeditationCreate,
    db: AsyncSession = Depends(get_db)
):
    # Validar que el tipo exista
    res = await db.execute(select(MeditationType).where(MeditationType.id == med_in.type_id))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tipo de meditación no válido")
    new = Meditation(**med_in.dict())
    db.add(new)
    await db.commit()
    await db.refresh(new)
    return new


@router.put(
    "/{meditation_id}",
    response_model=MeditationOut,
    dependencies=[Depends(check_admin_role)]
)
async def update_meditation(
    meditation_id: int,
    med_in: MeditationUpdate,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Meditation).where(Meditation.id == meditation_id))
    obj = res.scalar_one_or_none()
    if not obj: 
        raise HTTPException(status_code=404, detail="Meditación no encontrada")
    for field, val in med_in.dict(exclude_unset=True).items():
        setattr(obj, field, val)
    await db.commit()
    await db.refresh(obj)
    return obj


@router.delete(
    "/{meditation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_admin_role)]
)
async def delete_meditation(
    meditation_id: int,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Meditation).where(Meditation.id == meditation_id))
    obj = res.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Meditación no encontrada")
    await db.delete(obj)
    await db.commit()