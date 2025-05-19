
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.core.database import get_db
from app.models.models import MeditationSession, Meditation, User
from app.schemas.session_schemas import SessionCreate, SessionOut
from app.utils.security import get_current_user


router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("/", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Verifica si la meditación existe y carga el tipo de meditación
        res = await db.execute(
            select(Meditation)
            .options(selectinload(Meditation.meditation_type))
            .where(Meditation.id == payload.meditation_id)
        )
        meditation = res.scalar_one_or_none()
        if not meditation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Meditación con ID {payload.meditation_id} no encontrada"
            )
        
        new_sess = MeditationSession(
            user_id=current_user.id,
            meditation_id=payload.meditation_id,
            duration_completed=payload.duration_completed,
            date=payload.date
        )
        db.add(new_sess)
        await db.commit()
        await db.refresh(new_sess)
        
        # Cargar la meditación para la respuesta
        # Importante: asignamos el objeto meditation que ya tiene meditation_type cargado
        new_sess.meditation = meditation
        
        return new_sess
    
    except Exception as e:
        # Capturar cualquier otra excepción, hacer rollback y lanzar error amigable
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la sesión de meditación: {str(e)}"
        )


@router.get("/", response_model=list[SessionOut])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Cargar sesiones con sus relaciones completas
        query = (
            select(MeditationSession)
            .options(
                selectinload(MeditationSession.meditation)
                .selectinload(Meditation.meditation_type)
            )
            .where(MeditationSession.user_id == current_user.id)
            .order_by(MeditationSession.date.desc())
        )
        
        res = await db.execute(query)
        sessions = res.scalars().all()
        
        # Asegurarse de que todos los objetos relacionados estén accesibles
        # antes de salir del contexto asíncrono
        for sess in sessions:
            _ = sess.meditation
            if sess.meditation:
                _ = sess.meditation.meditation_type
                
        return sessions
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener las sesiones de meditación: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Cargar sesión con sus relaciones
        # Aseguramos que todas las relaciones necesarias estén cargadas completamente
        query = (
            select(MeditationSession)
            .options(
                selectinload(MeditationSession.meditation)
                .selectinload(Meditation.meditation_type)
            )
            .where(MeditationSession.id == session_id)
        )
        
        res = await db.execute(query)
        sess = res.scalar_one_or_none()
        
        if not sess or sess.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada"
            )
        
        # Asegurarse de que todos los objetos relacionados estén accesibles
        # antes de salir del contexto asíncrono
        _ = sess.meditation
        if sess.meditation:
            _ = sess.meditation.meditation_type
            
        return sess
    
    except HTTPException:
        # Re-lanzar excepciones HTTP que ya hemos definido
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la sesión de meditación: {str(e)}"
        )