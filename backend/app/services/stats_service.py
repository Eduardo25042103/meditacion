import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import List, Optional, Tuple


from app.models.models import (
    UserStats, MeditationSession, User, Meditation,
)
from app.schemas.stats_schemas import (
    StatsAnalysisOut, WeeklyStatsOut,
    MonthlyStatsOut, ProgressStatsOut, ChartOut, ChartDataPoint,
)


async def calculate_user_stats(user_id: int, db: AsyncSession) -> Optional[UserStats]:
    """Calcular stats básicas del user"""

    # Obtener todas las sesiones del usuario
    result = await db.execute(
         select(MeditationSession)
         .where(MeditationSession.user_id == user_id)
         .order_by(MeditationSession.date)
    )
    sessions = result.scalars().all()

    if not sessions:
        return None
    
    # Cálculos básicos
    total_minutes = sum(s.duration_completed for s in sessions)
    total_sessions = len(sessions)
    average_duration = total_minutes / total_sessions if total_sessions > 0 else 0

    # Calcular rachas usando pandas
    df = pd.DataFrame([{
        'date': s.date.date(),
        'duration': s.duration_completed
    } for s in sessions])
    
    # Agrupar por fecha (por si hay múltiples sesiones)
    daily_df = df.groupby('date').agg({
        'duration': 'sum'
    }).reset_index()

    # Calcular rachas
    current_streak, longest_streak = calculate_streaks(daily_df)

    # Buscar stats existentes o crear nuevos
    existing_result = await db.execute(
        select(UserStats).where(UserStats.user_id == user_id)
    )
    user_stats = existing_result.scalar_one_or_none()

    if user_stats:
        # Actualizar existentes
        user_stats.total_minutes = total_minutes
        user_stats.current_streak = current_streak
        user_stats.longest_streak = longest_streak
        # Solo actualizar si existen las columnas
        if hasattr(user_stats, 'total_session'):
            user_stats.total_sessions = total_sessions
        if hasattr(user_stats, 'average_session_duration'):
            user_stats.average_session_duration = average_duration
        if hasattr(user_stats, 'last_updated'):
            user_stats.last_updated = datetime.utcnow()
    
    else:
        # Crear nuevos - solo con campos básicos primero
        user_stats_data = {
            'user_id': user_id,
            'total_minutes': total_minutes,
            'current_streak': current_streak,
            'longest_streak': longest_streak
        }

        # Agregar campos opcionales si existen
        if hasattr(UserStats, 'total_sessions'):
            user_stats_data['total_sessions'] = total_sessions 
        if hasattr(UserStats, 'average_session_duration'):
            user_stats_data['average_session_duration'] = average_duration
        if hasattr(UserStats, 'last_updated'):
            user_stats_data['last_updated'] = datetime.utcnow()
        
        user_stats = UserStats(**user_stats_data)
        db.add(user_stats)
    
    await db.commit()
    await db.refresh(user_stats)        

    return user_stats


def calculate_streaks(daily_df: pd.DataFrame) -> Tuple[int, int]:
    """Calcular rachas actuales y más largas usando pandas"""
    if daily_df.empty:
        return 0, 0
    
    # Ordenar por fecha
    daily_df = daily_df.sort_values('date')

    # Crear rango completo de fechas desde la primera hasta hoy
    start_date = daily_df['date'].min()
    end_date = datetime.now().date()

    # Crear DataFrame con todas las fechas
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    full_df = pd.DataFrame({'date': date_range.date})

    # Hacer merge para identificar días con y sin meditación
    merged_df = full_df.merge(daily_df, on='date', how='left')
    merged_df['has_meditation'] = merged_df['duration'].notna()

    # Calcular rachas
    streaks = []
    current_streak = 0

    for has_meditation in merged_df['has_meditation']:
        if has_meditation:
            current_streak += 1
        else:
            if current_streak > 0:
                streaks.append(current_streak)
            current_streak = 0
    
    # Agregar la racha actual si termina en meditación
    if current_streak > 0:
        streaks.append(current_streak)

    # Calcular racha actual (desde el final hacia atrás)
    current_streak_days = 0
    for has_meditation in reversed(merged_df['has_meditation']):
        if has_meditation:
            current_streak_days += 1
        else:
            break
    
    longest_streak = max(streaks) if streaks else 0

    return current_streak_days, longest_streak


async def get_user_analytics(user_id: int, db: AsyncSession) -> StatsAnalysisOut:
    """Generar análisis detallado del usuario con pandas"""

    # Obtener sesiones con relaciones
    result = await db.execute(
        select(MeditationSession)
        .options(
            selectinload(MeditationSession.meditation)
            .selectinload(Meditation.meditation_type)
        )
        .where(MeditationSession.user_id == user_id)
        .order_by(MeditationSession.date)
    )
    sessions = result.scalars().all()

    if not sessions:
        # Retornar análisis vacío
        return StatsAnalysisOut(
            user_id=user_id,
            analysis_date=datetime.utcnow(),
            daily_average=0,
            weekly_average=0,
            monthly_average=0,
            most_active_day="N/A",
            most_active_hour=0,
            preferred_duration="N/A",
            meditation_type_distribution={},
            most_used_type="N/A",
            last_7_days_minutes=0,
            last_30_days_minutes=0,
            growth_rate_7d=0.0,
            growth_rate_30d=0.0,
            consistency_score=0.0,
            active_days_last_month=0,
            longest_gap_days=0
        )

    # Crear DataFrame
    df = pd.DataFrame([{
        'date': s.date,
        'duration': s.duration_completed,
        'meditation_type': s.meditation.meditation_type.name if s.meditation and s.meditation.meditation_type else 'Uknown',
        'day_of_week': s.date.strftime('%A'),
        'hour': s.date.hour,
        'weekday': s.date.weekday()
    } for s in sessions])

    # Convertir date a datetime si no lo está
    df['date'] = pd.to_datetime(df['date'])

    # Análisis temporal básico
    total_days = (df['date'].max() - df['date'].min()).days + 1
    daily_average = df['duration'].sum() / total_days if total_days > 0 else 0
    weekly_average = daily_average * 7
    monthly_average = daily_average * 30

    # Patrones de comportamiento
    day_analysis = df.groupby('day_of_week')['duration'].sum()
    most_active_day = day_analysis.idxmax() if not day_analysis.empty else "N/A"

    hour_analysis = df.groupby('hour')['duration'].sum()
    most_active_hour = hour_analysis.idxmax() if not hour_analysis.empty else 0

    # Duración preferida
    duration_bins = pd.cut(df['duration'], bins=[0, 10, 20, 30, float('inf')],
                           labels=['short', 'medium', 'long', 'extended'])
    preferred_duration = duration_bins.value_counts().idxmax() if not duration_bins.isna().all() else "N/A"

    # Análisis de tipos de meditación
    type_distribution = df['meditation_type'].value_counts().to_dict()
    most_used_type = df['meditation_type'].value_counts().idxmax() if not df.empty else "N/A"

    # Tendencias temporales
    now = datetime.now()
    last_7_days = df[df['date'] >= (now - timedelta(days=7))]
    last_30_days = df[df['date'] >= (now - timedelta(days=30))]

    last_7_days_minutes = last_7_days['duration'].sum()
    last_30_days_minutes = last_30_days['duration'].sum()

    # Calcular tasas de crecimiento (comparar con periodos anteriores)
    prev_7_days = df[(df['date'] >= (now - timedelta(days=14))) &
                     (df['date'] < (now - timedelta(days=7)))]
    prev_30_days = df[(df['date'] >= (now - timedelta(days=60))) &
                      (df['date'] < (now - timedelta(days=30)))]
    
    prev_7_minutes = prev_7_days['duration'].sum()
    prev_30_minutes = prev_30_days['duration'].sum()

    growth_rate_7d = ((last_7_days_minutes - prev_7_minutes) / prev_7_minutes * 100) if prev_7_minutes > 0 else 0
    growth_rate_30d = ((last_30_days_minutes - prev_30_minutes) / prev_30_minutes * 100) if prev_30_minutes > 0 else 0 

    # Métricas de consistencia
    daily_sessions = df.groupby(df['date'].dt.date).size()
    active_days_last_month = len(last_30_days.groupby(last_30_days['date'].dt.date))
    consistency_score = (active_days_last_month / 30) * 100

    # Calcular mayor brecha
    daily_dates = sorted(df['date'].dt.date.unique())
    gaps = []
    for i in range(1, len(daily_dates)):
        gap = (daily_dates[i] - daily_dates[i-1]).days - 1
        if gap > 0:
            gaps.append(gap)
    
    longest_gap_days = max(gaps) if gaps else 0

    return StatsAnalysisOut(
        user_id=user_id,
        analysis_date=datetime.utcnow(),
        daily_average=round(daily_average, 2),
        weekly_average=round(weekly_average, 2),
        monthly_average=round(monthly_average, 2),
        most_active_day=most_active_day,
        most_active_hour=int(most_active_hour),
        preferred_duration=str(preferred_duration),
        meditation_type_distribution=type_distribution,
        most_used_type=most_used_type,
        last_7_days_minutes=int(last_7_days_minutes),
        last_30_days_minutes=int(last_30_days_minutes),
        growth_rate_7d=round(growth_rate_7d, 2),
        growth_rate_30d=round(growth_rate_30d, 2),
        consistency_score=round(consistency_score, 2),
        active_days_last_month=active_days_last_month,
        longest_gap_days=longest_gap_days
    )


async def group_sessions_by_week(sessions: List[MeditationSession]) -> List[WeeklyStatsOut]:
    """Agrupar sesiones por semana usando pandas"""
    if not sessions:
        return []
    
    # Crear DataFrame
    df = pd.DataFrame([{
        'date': s.date,
        'duration': s.duration_completed,
        'meditation_type': s.meditation.meditation_type.name if s.meditation and s.meditation.meditation_type else "Unknown"
    } for s in sessions])

    df['date'] = pd.to_datetime(df['date'])
    df['week'] = df['date'].dt.to_period('W')

    # Agrupar por semana
    weekly_groups = df.groupby('week')

    weekly_stats = []
    for week, group in weekly_groups:
        week_start = week.start_time.to_pydatetime()
        week_end = week.end_time.to_pydatetime()

        total_minutes = group['duration'].sum()
        total_sessions = len(group)
        average_duration = group['duration'].mean()
        days_practiced = group['date'].dt.date.nunique()

        # Tipo más usado
        type_counts = group['meditation_type'].value_counts()
        most_used_type = type_counts.index[0] if not type_counts.empty else None

        weekly_stats.append(WeeklyStatsOut(
            week_start=week_start,
            week_end=week_end,
            total_minutes=int(total_minutes),
            total_sessions=total_sessions,
            average_duration=float(average_duration),
            days_practiced=days_practiced,
            most_used_type=most_used_type    
        ))

        return weekly_stats
    

async def group_sessions_by_month(sessions: List[MeditationSession]) -> List[MonthlyStatsOut]:
    """Agrupar sesiones por mes usando pandas"""
    if not sessions:
        return []
    
    # Crear DataFrame
    df = pd.DataFrame([{
        'date': s.date,
        'duration': s.duration_completed,
        'meditation_type': s.meditation.meditation_type.name if s.meditation and s.meditation_meditation_type else "Unknown"
    } for s in sessions])

    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')

    # Agrupar por mes
    monthly_groups = df.groupby('month')

    monthly_stats = []
    for month, group in monthly_groups:
        month_start = month.start_time.to_pydatetime()

        total_minutes = group['duration'].sum()
        total_sessions = len(group)
        average_duration = group['duration'].mean()
        days_practiced = group['date'].dt.date.nunique()

        # Tipo más usado
        type_counts = group['meditation_type'].value_counts()
        most_used_type = type_counts.index[0] if not type_counts.empty else None

        # Calcular días consecutivos en el mes
        daily_sessions = group.groupby(group['date'].dt.date).size()
        streak_days = calculate_monthly_streak(daily_sessions)

        monthly_stats.append(MonthlyStatsOut(
            month=month_start.month,
            year=month_start.year,
            month_name=month_start.strftime('%B'),
            total_minutes=int(total_minutes),
            total_sessions=total_sessions,
            average_duration=float(average_duration),
            days_practiced=days_practiced,
            most_used_type=most_used_type,
            streak_days=streak_days
        ))


def calculate_monthly_streak(daily_sessions: pd.Series) -> int:
    """Calcular la racha más larga dentro de un mes"""
    dates = sorted(daily_sessions.index)
    max_streak = 0
    current_streak = 1

    for i in range(1, len(dates)):
        if (dates[i] - dates[i-1]).days == 1:
            current_streak += 1
        else:
            max_streak = max(max_streak, current_streak)
            current_streak = 1

    return max(max_streak, current_streak)


async def analyze_user_progress(sessions: List[MeditationSession], days: int) -> ProgressStatsOut:
    """Analizar progreso del usuario"""
    if not sessions:
        return ProgressStatsOut(
            period_days=days,
            total_minutes=0,
            total_sessions=0,
            average_daily_minutes=0.0,
            consistency_percentage=0.0,
            improvement_trend="stable",
            best_day=None,
            best_day_minutes=0,
            meditation_types_used=[],
            favorite_time_slot="N/A"
        )
    
    # Crear DataFrame
    df = pd.DataFrame([{
        'date': s.date,
        'duration': s.duration_completed,
        'meditation_type': s.meditation.meditation_type.name if s.meditation and s.meditation_type else "Unknown"
    } for s in sessions])

    df['date'] = pd.to_datetime(df['date'])

    # Estadísticas básicas
    total_minutes = df['duration'].sum()
    total_sessions = len(df)
    average_daily_minutes = total_minutes / days

    # Consistencia
    unique_days = df['date'].dt.date.nunique()
    consistency_percentage = (unique_days / days) * 100

    # Mejor día
    daily_totals = df.groupby(df['date'].dt.date)['duration'].sum()
    best_day = daily_totals.idxmax() if not daily_totals.empty else None
    best_day_minutes = daily_totals.max() if not daily_totals.empty else None

    # Tipos de meditación usados
    meditation_types_used = df['meditation_type'].unique().tolist()

    # Franja horaria favorita
    hour_bins = pd.cut(df['hour'], bins=[0, 5, 11, 17, 24],
                       labels=['Evening', 'Morning', 'Afternoon', 'Evening'],
                       ordered=False)
    favorite_time_slot = hour_bins.value_counts().idxmax() if not hour_bins.isna().all() else "N/A"

    # Tendencia de mejora (comparar primera y segunda mitad)
    mid_point = len(df) // 2
    if mid_point > 0:
        first_half = df.iloc[:mid_point]['duration'].mean()
        second_half = df.iloc[mid_point:]['duration'].mean()

        if second_half > first_half * 1.1:
            improvement_trend = "improving"
        elif second_half < first_half * 0.9:
            improvement_trend = "declining"
        else:
            improvement_trend = "stable"
    
    else:
        improvement_trend = "stable"

    return ProgressStatsOut(
        period_days=days,
        total_minutes=int(total_minutes),
        total_sessions=total_sessions,
        average_daily_minutes=round(average_daily_minutes, 2),
        consistency_percentage=round(consistency_percentage, 2),
        improvement_trend=improvement_trend,
        best_day=datetime.combine(best_day, datetime.min.time()) if best_day else None,
        best_day_minutes=int(best_day_minutes),
        meditation_types_used=meditation_types_used,
        favorite_time_slot=str(favorite_time_slot)
    )


async def generate_stats_charts(user_id: int, chart_type: str, db: AsyncSession) -> ChartOut:
    """Generar datos para gráficos usando schemas apropiados"""

    # Obtener sesiones
    result = await db.execute(
        select(MeditationSession)
        .options(
            selectinload(MeditationSession.meditation)
            .selectinload(Meditation.meditation_type)
        )
        .where(MeditationSession.user_id == user_id)
        .order_by(MeditationSession.date)
    )
    sessions = result.scalars().all()

    if not sessions:
        return ChartOut(
            chart_type="empty",
            title="Sin datos disponibles",
            data=[],
            labels=None,
            colors=None,
            metadata={"message": "No hay datos para generar gráficos"}
        )
    
    # Crear DataFrame
    df = pd.DataFrame([{
        'date': s.date,
        'duration': s.duration_completed,
        'meditation_type': s.meditation.meditation_type.name if s.meditation and s.meditation.meditation_type else "Unknown"   
    } for s in sessions])

    df['date'] = pd.to_datetime(df['date'])

    if chart_type == "progress":
        # Gráfico de progreso temporal
        daily_totals = df.groupby(df['date'].dt.date)['duration'].sum().reset_index()
        
        data_points = [
            ChartDataPoint(
                x=row['date'].isoformat(),
                y=row['duration'],
                label=f"{row['duration']} min"
            )
            for _, row in daily_totals.iterrows()
        ]
        
        return ChartOut(
            chart_type="line",
            title="Progreso de Meditación Diaria",
            data=data_points,
            labels=["Fecha", "Minutos"],
            colors=["#4F46E5"],
            metadata={
                "total_days": len(daily_totals),
                "avg_minutes": daily_totals['duration'].mean()
            }
        )
    
    elif chart_type == "types":
        # Gráfico de distribución por tipos
        type_totals = df.groupby('meditation_type')['duration'].sum()
        
        # Colores predefinidos para tipos
        colors = ["#4F46E5", "#059669", "#DC2626", "#D97706", "#7C3AED"]
        
        data_points = [
            ChartDataPoint(
                x=type_name,
                y=int(minutes),
                label=f"{type_name}: {minutes} min"
            )
            for type_name, minutes in type_totals.items()
        ]
        
        return ChartOut(
            chart_type="pie",
            title="Distribución por Tipo de Meditación",
            data=data_points,
            labels=list(type_totals.index),
            colors=colors[:len(type_totals)],
            metadata={
                "total_types": len(type_totals),
                "most_used": type_totals.idxmax(),
                "total_minutes": type_totals.sum()
            }
        )
    
    elif chart_type == "weekly":
        # Gráfico semanal
        df['week'] = df['date'].dt.to_period('W')
        weekly_totals = df.groupby('week')['duration'].sum().reset_index()
        weekly_totals['week_str'] = weekly_totals['week'].astype(str)

        data_points = [
            ChartDataPoint(
                x=row['week_str'],
                y=int(row['duration']),
                label=f"Semana {row['week_str']}: {row['duration']} min"
            )
            for _, row in weekly_totals.iterrows()
        ]
        
        return ChartOut(
            chart_type="bar",
            title="Minutos por Semana",
            data=data_points,
            labels=["Semana", "Minutos"],
            colors=["#059669"],
            metadata={
                "total_weeks": len(weekly_totals),
                "avg_weekly": weekly_totals['duration'].mean(),
                "best_week": weekly_totals.loc[weekly_totals['duration'].idxmax(), 'week_str']
            }
        )
    
    elif chart_type == "monthly":
        # Gráfico mensual
        df['month'] = df['date'].dt.to_period('M')
        monthly_totals = df.groupby('month')['duration'].sum().reset_index()
        monthly_totals['month_str'] = monthly_totals['month'].dt.strftime('%Y-%m')

        data_points = [
            ChartDataPoint(
                x=row['month_str'],
                y=int(row['duration']),
                label=f"{row['month_str']}: {row['duration']} min"
            )
            for _, row in monthly_totals.iterrows()
        ]
        
        return ChartOut(
            chart_type="bar",
            title="Minutos por Mes",
            data=data_points,
            labels=["Mes", "Minutos"],
            colors=["#DC2626"],
            metadata={
                "total_months": len(monthly_totals),
                "avg_monthly": monthly_totals['duration'].mean(),
                "growth_trend": "improving" if monthly_totals['duration'].iloc[-1] > monthly_totals['duration'].iloc[0] else "stable"
            }
        )
    
    else:
        return ChartOut(
            chart_type="error",
            title="Tipo de gráfico no válido",
            data=[],
            labels=None,
            colors=None,
            metadata={"error": f"Tipo '{chart_type}' no soportado"}
        )


# También actualizar el endpoint para usar el tipo correcto
async def get_user_charts(user_id: int, chart_type: str, db: AsyncSession) -> ChartOut:
    """Endpoint mejorado que retorna ChartOut"""
    return await generate_stats_charts(user_id, chart_type, db)

async def refresh_all_user_stats(db: AsyncSession) -> int:
    """Recalcular estadísticas de todos los usuarios"""

    # Obtener todos los usuarios con sesiones
    result = await db.execute(
        select(User)
        .join(MeditationSession)
        .distinct()
    )
    users = result.scalars().all()

    refreshed_count = 0

    for user in users:
        try:
            await calculate_user_stats(user.id, db)
            refreshed_count += 1
        except Exception as e:
            # Log error pero continúa con el siguiente usuario
            print(f"Error refreshing stats for user {user.id}: {e}")
            continue
    
    return refreshed_count