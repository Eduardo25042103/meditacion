from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.core.database import get_db
from app.models.models import UserStats, MeditationSession, User, Meditation, MeditationType
from app.schemas.stats_schemas import (
    UserStatsOut, StatsAnalysisOut, WeeklyStatsOut, 
    MonthlyStatsOut, ProgressStatsOut, ChartOut
)
from app.utils.security import get_current_user, check_admin_role
from app.services.stats_service import (
    calculate_user_stats, get_user_analytics, 
    generate_stats_charts, refresh_all_user_stats
)

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/", response_model=UserStatsOut)
async def get_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener estadísticas básicas del usuario actual"""
    try:
        # Buscar stats existentes
        result = await db.execute(
            select(UserStats).where(UserStats.user_id == current_user.id)
        )
        user_stats = result.scalar_one_or_none()
        
        # Si no existen stats, calcularlas
        if not user_stats:
            user_stats = await calculate_user_stats(current_user.id, db)
            if not user_stats:
                # Usuario sin sesiones se crean stats vacías
                return UserStatsOut(
                    id=0,
                    user_id=current_user.id,
                    total_minutes=0,
                    current_streak=0,
                    longest_streak=0,
                    total_sessions=0, 
                    average_session_duration=0.0,
                    last_updated=datetime.utcnow()
                )
        
        return user_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/analysis", response_model=StatsAnalysisOut)
async def get_user_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener análisis detallado con pandas de las sesiones del usuario"""
    try:
        analysis = await get_user_analytics(current_user.id, db)
        return analysis
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar análisis: {str(e)}"
        )


@router.get("/charts", response_model=ChartOut) 
async def get_user_charts(
    chart_type: str = "progress",  # progress, weekly, monthly, types
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generar gráficos de estadísticas del usuario"""
    try:
        chart_data = await generate_stats_charts(current_user.id, chart_type, db)
        return chart_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar gráficos: {str(e)}"
        )


@router.get("/weekly", response_model=List[WeeklyStatsOut])
async def get_weekly_stats(
    weeks: int = 4,  # Últimas 4 semanas por defecto
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener estadísticas semanales del usuario"""
    try:
        # Calcular fechas
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(weeks=weeks)
        
        # Obtener sesiones del período
        result = await db.execute(
            select(MeditationSession)
            .options(
                selectinload(MeditationSession.meditation)
                .selectinload(Meditation.meditation_type)
            )
            .where(
                MeditationSession.user_id == current_user.id,
                MeditationSession.date >= start_date,
                MeditationSession.date <= end_date
            )
            .order_by(MeditationSession.date)
        )
        
        sessions = result.scalars().all()
        
        # Agrupar por semanas usando pandas
        from app.services.stats_service import group_sessions_by_week
        weekly_stats = await group_sessions_by_week(sessions)
        
        return weekly_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas semanales: {str(e)}"
        )


@router.get("/monthly", response_model=List[MonthlyStatsOut])
async def get_monthly_stats(
    months: int = 6,  # Últimos 6 meses por defecto
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener estadísticas mensuales del usuario"""
    try:
        # Calcular fechas
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months * 30)
        
        # Obtener sesiones del período
        result = await db.execute(
            select(MeditationSession)
            .options(
                selectinload(MeditationSession.meditation)
                .selectinload(Meditation.meditation_type)
            )
            .where(
                MeditationSession.user_id == current_user.id,
                MeditationSession.date >= start_date,
                MeditationSession.date <= end_date
            )
            .order_by(MeditationSession.date)
        )
        
        sessions = result.scalars().all()
        
        # Agrupar por meses usando pandas
        from app.services.stats_service import group_sessions_by_month
        monthly_stats = await group_sessions_by_month(sessions)
        
        return monthly_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas mensuales: {str(e)}"
        )


@router.get("/progress", response_model=ProgressStatsOut)
async def get_progress_stats(
    days: int = 30,  # Últimos 30 días por defecto
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener estadísticas de progreso del usuario"""
    try:
        # Calcular fechas
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Obtener sesiones del período
        result = await db.execute(
            select(MeditationSession)
            .options(
                selectinload(MeditationSession.meditation)
                .selectinload(Meditation.meditation_type)
            )
            .where(
                MeditationSession.user_id == current_user.id,
                MeditationSession.date >= start_date,
                MeditationSession.date <= end_date
            )
            .order_by(MeditationSession.date)
        )
        
        sessions = result.scalars().all()
        
        # Analizar progreso usando pandas
        from app.services.stats_service import analyze_user_progress
        progress_stats = await analyze_user_progress(sessions, days)
        
        return progress_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas de progreso: {str(e)}"
        )


@router.post("/refresh", status_code=200)
async def refresh_user_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Forzar recálculo de estadísticas del usuario desde cero"""
    try:
        # Eliminar stats existentes
        result = await db.execute(
            select(UserStats).where(UserStats.user_id == current_user.id)
        )
        existing_stats = result.scalar_one_or_none()
        
        if existing_stats:
            await db.delete(existing_stats)
            await db.commit()
        
        # Recalcular estadísticas
        new_stats = await calculate_user_stats(current_user.id, db)
        
        if not new_stats:
            return {
                "message": "No hay sesiones para calcular estadísticas",
                "stats_refreshed": False
            }
        
        # Corregir acceso a atributos usando hasattr
        stats_dict = {
            "total_minutes": new_stats.total_minutes,
            "current_streak": new_stats.current_streak,
            "longest_streak": new_stats.longest_streak
        }
        
        # Agregar campos opcionales si existen
        if hasattr(new_stats, 'total_sessions'):
            stats_dict["total_sessions"] = new_stats.total_sessions
        if hasattr(new_stats, 'average_session_duration'):
            stats_dict["average_session_duration"] = new_stats.average_session_duration
        
        return {
            "message": "Estadísticas recalculadas exitosamente",
            "stats_refreshed": True,
            "stats": stats_dict
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al recalcular estadísticas: {str(e)}"
        )


@router.post("/refresh-all", status_code=200)
async def refresh_all_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_admin_role)  # Solo admins
):
    """Recalcular estadísticas de todos los usuarios (Solo admins)"""
    try:
        refreshed_count = await refresh_all_user_stats(db)
        
        return {
            "message": f"Estadísticas recalculadas para {refreshed_count} usuarios",
            "users_processed": refreshed_count
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al recalcular todas las estadísticas: {str(e)}"
        )


@router.get("/all", response_model=List[UserStatsOut])
async def get_all_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_admin_role)  # Solo admins
):
    """Obtener estadísticas de todos los usuarios (Solo admins)"""
    try:
        result = await db.execute(
            select(UserStats)
            .options(selectinload(UserStats.user))
            .order_by(UserStats.total_minutes.desc())
        )
        
        all_stats = result.scalars().all()
        return all_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener todas las estadísticas: {str(e)}"
        )