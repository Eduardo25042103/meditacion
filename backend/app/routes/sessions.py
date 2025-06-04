from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.core.database import get_db
from app.models.models import MeditationSession, Meditation, User
from app.schemas.session_schemas import SessionCreate, SessionOut
from app.utils.security import get_current_user, check_admin_role
from app.services.preferences_service import update_user_preferences



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

        #Actualizamos preferencias
        await update_user_preferences(current_user.id, db)

        
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
        # Base query con todas las relaciones cargadas
        base_query = (
            select(MeditationSession)
            .options(
                selectinload(MeditationSession.meditation)
                .selectinload(Meditation.meditation_type),
                selectinload(MeditationSession.user)  # Cargar usuario para admins
            )
            .order_by(MeditationSession.date.desc())
        )
        
        # Si es admin, ve todas las sesiones; si es usuario normal, solo las suyas
        if current_user.role == "admin":
            query = base_query
        else:
            query = base_query.where(MeditationSession.user_id == current_user.id)
        
        res = await db.execute(query)
        sessions = res.scalars().all()
        
        # Se asegura de que todos los objetos relacionados estén accesibles
        # antes de salir del contexto asíncrono
        for sess in sessions:
            _ = sess.meditation
            if sess.meditation:
                _ = sess.meditation.meditation_type
            # Para admins, también cargar info del usuario
            if current_user.role == "admin":
                _ = sess.user
                
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
        # Asegura que todas las relaciones necesarias estén cargadas completamente
        query = (
            select(MeditationSession)
            .options(
                selectinload(MeditationSession.meditation)
                .selectinload(Meditation.meditation_type),
                selectinload(MeditationSession.user)  # Para admins
            )
            .where(MeditationSession.id == session_id)
        )
        
        res = await db.execute(query)
        sess = res.scalar_one_or_none()
        
        # Verificar existencia de la sesión
        if not sess:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada"
            )
        
        if current_user.role != "admin" and sess.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver esta sesión"
            )
        
        # Se asegura de que todos los objetos relacionados estén accesibles
        # antes de salir del contexto asíncrono
        _ = sess.meditation
        if sess.meditation:
            _ = sess.meditation.meditation_type
        _ = sess.user
            
        return sess
    
    except HTTPException:
        # Re-lanzar excepciones HTTP que ya definí
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la sesión de meditación: {str(e)}"
        )

@router.patch(
    "/{session_id}",
    response_model=SessionOut,
    summary="Retomar o actualizar parcialmente una meditación propia"
)
async def update_session(
    session_id: int,
    payload: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # Traer la sesión y verificar que sea del usuario
        stmt = (
            select(MeditationSession)
            .options(
                selectinload(MeditationSession.meditation)
                .selectinload(Meditation.meditation_type)
            )
            .where(MeditationSession.id == session_id)
        )    
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
    
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada"
            )
            
        # Solo el propietario de la sesión o un admin pueden actualizarla
        if session.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes actualizar tus propias sesiones"
            )
    
        # Actualizar solo los campos permitidos
        session.duration_completed = payload.duration_completed
        await db.commit()
        await db.refresh(session)

        # Actualizar preferencias después de modificar la sesión
        await update_user_preferences(session.user_id, db)

        # Asegura que las relaciones sean accesibles antes de la serialización
        _ = session.meditation
        if session.meditation:
            _ = session.meditation.meditation_type

        return session
        
    except HTTPException:
        raise

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la sesión de meditación: {str(e)}"
        )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una sesión (solo admin)",
    dependencies=[Depends(check_admin_role)],
)
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        # Buscar la sesión que se va a eliminar
        stmt = select(MeditationSession).where(MeditationSession.id == session_id)
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión no encontrada"
            )
        
        # Guardar el user_id antes de eliminar la sesión
        user_id = session.user_id
        
        # Eliminar la sesión
        await db.delete(session)
        await db.commit()
        
        # Actualizar las preferencias del usuario después de la eliminación
        await update_user_preferences(user_id, db)
        
    except HTTPException:
        # Re-lanzar excepciones HTTP que ya definí
        raise
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar la sesión de meditación: {str(e)}"
        )