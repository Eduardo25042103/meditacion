from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List


from app.core.database import get_db
from app.models.models import Meditation, MeditationType
from app.schemas.meditation_schemas import MeditationCreate, MeditationUpdate, MeditationOut
from app.utils.security import check_admin_role


router = APIRouter(prefix="/meditations", tags=["Meditations"])


@router.get("/", response_model=List[MeditationOut])
async def list_meditations(db: AsyncSession = Depends(get_db)):
    # Carga las meditaciones con sus relaciones
    result = await db.execute(
        select(Meditation).options(
            selectinload(Meditation.meditation_type)
        )
    )
    
    # Usa directamente el modelo de respuesta Pydantic
    meditations = result.scalars().all()
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
    try:
        # Validar que el tipo exista
        res = await db.execute(
            select(MeditationType).where(MeditationType.id == med_in.type_id)
        )
        meditation_type = res.scalar_one_or_none()
        if not meditation_type:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Tipo de meditación con ID {med_in.type_id} no encontrado"
            )
        
        # Crear la meditación
        new = Meditation(**med_in.dict())
        db.add(new)
        await db.commit()
        await db.refresh(new)
        
        # Cargar el tipo de meditación directamente en el objeto
        new.meditation_type = meditation_type
        
        return new
        
    except Exception as e:
        # Capturar cualquier otra excepción, hacer rollback y lanzar error amigable
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la meditación: {str(e)}"
        )


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
    try:
        # Buscar la meditación con su tipo ya cargado
        res = await db.execute(
            select(Meditation)
            .options(selectinload(Meditation.meditation_type))
            .where(Meditation.id == meditation_id)
        )
        obj = res.scalar_one_or_none()
        if not obj: 
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Meditación con ID {meditation_id} no encontrada"
            )
        
        # Validar el type_id si se está actualizando
        update_data = med_in.dict(exclude_unset=True)
        if "type_id" in update_data:
            type_res = await db.execute(
                select(MeditationType).where(MeditationType.id == update_data["type_id"])
            )
            meditation_type = type_res.scalar_one_or_none()
            if not meditation_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tipo de meditación con ID {update_data['type_id']} no encontrado"
                )
            # Actualizar la relación directamente
            obj.meditation_type = meditation_type
        
        # Actualizar campos
        for field, val in update_data.items():
            setattr(obj, field, val)
        
        # Guardar cambios
        await db.commit()
        await db.refresh(obj)
        
        return obj
        
    except Exception as e:
        # Capturar cualquier otra excepción, hacer rollback y lanzar error amigable
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la meditación: {str(e)}"
        )


@router.delete(
    "/{meditation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(check_admin_role)]
)
async def delete_meditation(
    meditation_id: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        res = await db.execute(select(Meditation).where(Meditation.id == meditation_id))
        obj = res.scalar_one_or_none()
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Meditación con ID {meditation_id} no encontrada"
            )
        await db.delete(obj)
        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la meditación: {str(e)}"
        )