from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from collections import Counter
from datetime import datetime


from app.models.models import MeditationSession, Meditation, UserPreferences


async def update_user_preferences(user_id: int, db: AsyncSession):
    # Trae las sessions con su meditación y tags
    stmt = (
        select(MeditationSession)
        .options(
            selectinload(MeditationSession.meditation)
            .selectinload(Meditation.meditation_type)
        )
        .where(MeditationSession.user_id == user_id)
    )
    res = await db.execute(stmt)
    sessions = res.scalars().all()

    # Busca preferencias existentes
    stmt2 = select(UserPreferences).where(UserPreferences.user_id == user_id)
    res2 = await db.execute(stmt2)
    prefs = res2.scalar_one_or_none()

    # Si no hay sesiones, se eliminan las preferencias
    if not sessions:
        if prefs:
            await db.delete(prefs)
            await db.commit()
        return 
    

    # Duración promedio
    total = sum(s.duration_completed for s in sessions)
    avg = total / len(sessions)
    if avg <= 10:
        pref_duration = "short"
    elif avg <= 15:
        pref_duration = "medium"
    else:
        pref_duration = "long"
    

    # Franja horaria más frecuente
    hours = [s.date.hour for s in sessions]
    def slot(h):
        if 5 <= h < 12: return "morning"
        if 12 <= h < 18: return "afternoon"
        return "evening"
    slots = [slot(h) for h in hours]
    pref_time = Counter(slots).most_common(1)[0][0]


    # Tags más comunes
    tags = []
    for s in sessions:
        tags += (s.meditation.meditation_type.tags or [])
    top_goals = [t for t, _ in Counter(tags).most_common(3)]


    # Upsert en UserPreferences
    
    if prefs:
        prefs.preferred_duration = pref_duration
        prefs.preferred_time = pref_time
        prefs.goals = top_goals
    else:
        prefs = UserPreferences(
            user_id=user_id,
            preferred_duration=pref_duration,
            preferred_time=pref_time,
            goals=top_goals
        )
        db.add(prefs)

    await db.commit()