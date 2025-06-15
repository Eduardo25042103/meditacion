from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.schemas.auth_schemas import UserResponse


class UserStatsBase(BaseModel):
    total_minutes: int = Field(default=0, description="Total de minutos meditados")
    current_streak: int = Field(default=0, description="Racha actual de días consecutivos")
    longest_streak: int = Field(default=0, description="Racha más larga de días consecutivos")
    total_sessions: int = Field(default=0, description="Total de sesiones completadas")
    average_session_duration: float = Field(default=0.0, description="Duración promedio por sesión")


class UserStatsOut(UserStatsBase):
    id: int
    user_id: int
    last_updated: Optional[datetime] = None
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True
        orm_mode = True


class WeeklyStatsOut(BaseModel):
    week_start: datetime = Field(description="Inicio de semana")
    week_end: datetime = Field(description="Fin de semana")
    total_minutes: int = Field(description="Minutos totales de la semana")
    total_sessions: int = Field(description="Sesiones totales de la semana")
    average_duration: float = Field(description="Duración promedio por sesión")
    days_practiced: int = Field(description="Días que meditó en la semana")
    most_used_type: Optional[str] = Field(description="Tipo de meditación más usado")


class MonthlyStatsOut(BaseModel):
    month: int = Field(description="Mes (1-12)")
    year: int = Field(description="Año")
    month_name: str = Field(description="Nombre del mes")
    total_minutes: int = Field(description="Minutos totales del mes")
    total_sessions: int = Field(description="Sesiones totales del mes")
    average_duration: float = Field(description="Duración promedio por sesión")
    days_practiced: int = Field(description="Días que meditó en el mes")
    most_used_type: Optional[str] = Field(description="Tipo de meditación más usado")
    streak_days: int = Field(description="Días consecutivos en el mes")


class ProgressStatsOut(BaseModel):
    period_days: int = Field(description="Días del periodo analizados")
    total_minutes: int = Field(description="Minutos totales del periodo")
    total_sessions: int = Field(description="Sesiones totales del periodo")
    average_daily_minutes: float = Field(description="Promedio de minutos por día")
    consistency_percentage: float = Field(description="Porcentaje de días con meditación")
    improvement_trend: str = Field("Tendencia: improving, stable, declining")
    best_day: Optional[datetime] = Field(description="Día con más minutos")
    best_day_minutes: int = Field(description="Día con más minutos")
    meditation_types_used: List[str] = Field(description="Tipos de meditación utilizados")
    favorite_time_slot: str = Field(description="Franja horaria preferida")


class StatsAnalysisOut(BaseModel):
    user_id: int
    analysis_date: datetime

    # Análisis temporal
    daily_average: float = Field(description="Promedio diario de minutos")
    weekly_average: float = Field(description="Promedio semanal de minutos")
    monthly_average: float = Field(description="Promedio mensual de minutos")

    # Patrones de comportamiento
    most_active_day: str = Field(description="Día de la semana más activo")
    most_active_hour: int = Field(description="Hora más activa del día")
    preferred_duration: str = Field(description="Duración preferida de sesión")

    # Análisis de tipos de meditación
    meditation_type_distribution: Dict[str, int] = Field(description="Distribución por tipo")
    most_used_type: str = Field(description="Tipo más utilizado")

    # Tendencias temporales
    last_7_days_minutes: int = Field(description="Minutos últimos 7 días")
    last_30_days_minutes: int = Field(description="Minutos últimos 30 días")
    growth_rate_7d: float = Field(description="Tasa crecimiento últimos 7 días (%)")
    growth_rate_30d: float = Field(description="Tasa crecimiento últimos 30 días (%)")

    # Métricas de consistencia
    consistency_score: float = Field(description="Puntuación de consistencia (0-100)")
    active_days_last_month: int = Field(description="Días activos último mes")
    longest_gap_days: int = Field(description="Mayor brecha sin meditar (días)")

class ChartDataPoint(BaseModel):
    x: Any = Field(description="Valor eje X")
    y: Any = Field(description="Valor eje Y")
    label: Optional[str] = Field(description="Etiqueta opcional")

class ChartOut(BaseModel):
    chart_type: str = Field(description="Tipo de gráfico")
    title: str = Field(description="Título del gráfico")
    data: List[ChartDataPoint] = Field(description="Datos del gráfico")
    labels: Optional[List[str]] = Field(description="Etiquetas para ejes")
    colors: Optional[List[str]] = Field(description="Colores para el gráfico")
    metadata: Optional[Dict[str, Any]] = Field(description="Metadatos adicinoales")

# Para respuestas de endpoints específicos
class StatsRefreshResponse(BaseModel):
    message: str
    stats_refreshed: bool
    stats: Optional[Dict[str, Any]] = None

class AllStatsRefreshResponse(BaseModel):
    message: str
    users_processed: int