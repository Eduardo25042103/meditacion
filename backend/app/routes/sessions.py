from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
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
    # Verifica si la meditación existe
    res = await db.execute(select(Meditation).where(Meditation.id == payload.meditation_id))
    if not res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Meditación no encontrada"
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
    return new_sess


@router.get("/", response_model=list[SessionOut])
async def list_sessions(
    db: AsyncSession=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(
        select(MeditationSession)
        .where(MeditationSession.user_id == current_user.id)
        .order_by(MeditationSession.date.desc())
    )
    return res.scalars().all()


@router.get("/{session_id}", response_model=SessionOut)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    res = await db.execute(select(MeditationSession).where(MeditationSession.id == session_id))
    sess = res.scalar_one_or_none()
    if not sess or sess.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada"
        )
    return sess