from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any


from app.core.database import get_db
from app.models.models import Meditation, MeditationType
from app.schemas.meditation_schemas import MeditationCreate, MeditationUpdate, MeditationOut
from app.utils.security import check_admin_role


router = APIRouter(prefix="/meditations", tags=["Meditations"])


# Función auxiliar para convertir un modelo a diccionario
def meditation_to_dict(meditation, meditation_type=None) -> Dict[str, Any]:
    """Convierte un objeto Meditation y su MeditationType relacionado a un diccionario."""
    if meditation_type is None:
        meditation_type = meditation.meditation_type
    
    return {
        "id": meditation.id,
        "title": meditation.title,
        "duration": meditation.duration,
        "difficulty": meditation.difficulty,
        "type_id": meditation.type_id,
        "meditation_type": {
            "id": meditation_type.id,
            "name": meditation_type.name,
            "description": meditation_type.description,
            "duration_range": meditation_type.duration_range,
            "tags": meditation_type.tags
        }
    }


@router.get("/", response_model=List[MeditationOut])
async def list_meditations(db: AsyncSession = Depends(get_db)):
    # Cargamos las meditaciones con sus relaciones
    result = await db.execute(
        select(Meditation).options(
            selectinload(Meditation.meditation_type)
        )
    )
    
    # Convertir los resultados a diccionarios
    meditations = []
    for med in result.scalars().all():
        meditations.append(meditation_to_dict(med))
    
    return meditations


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
    meditation_type = res.scalar_one_or_none()
    if not meditation_type:
        raise HTTPException(status_code=400, detail="Tipo de meditación no válido")
    
    # Crear la meditación
    new = Meditation(**med_in.dict())
    db.add(new)
    await db.commit()
    await db.refresh(new)
    
    # Convertir a diccionario para la respuesta
    return meditation_to_dict(new, meditation_type)


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
    # Buscar la meditación
    res = await db.execute(select(Meditation).where(Meditation.id == meditation_id))
    obj = res.scalar_one_or_none()
    if not obj: 
        raise HTTPException(status_code=404, detail="Meditación no encontrada")
    
    # Actualizar campos
    update_data = med_in.dict(exclude_unset=True)
    for field, val in update_data.items():
        setattr(obj, field, val)
    
    # Guardar cambios
    await db.commit()
    await db.refresh(obj)
    
    # Obtener tipo de meditación
    type_res = await db.execute(select(MeditationType).where(MeditationType.id == obj.type_id))
    meditation_type = type_res.scalar_one_or_none()
    
    # Convertir a diccionario para la respuesta
    return meditation_to_dict(obj, meditation_type)


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