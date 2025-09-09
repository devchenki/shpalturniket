"""
Router для управления темами
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..core.db import get_session
from ..models.theme import ThemePreset


router = APIRouter()


@router.get("/themes", response_model=List[ThemePreset], summary="Получить все темы")
async def list_themes(session: Session = Depends(get_session)):
    return session.exec(select(ThemePreset)).all()


@router.post("/themes", response_model=ThemePreset, status_code=201, summary="Создать тему")
async def create_theme(preset: ThemePreset, session: Session = Depends(get_session)):
    # Проверка уникальности имени
    existing = session.exec(select(ThemePreset).where(ThemePreset.name == preset.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Тема с таким именем уже существует")
    session.add(preset)
    session.commit()
    session.refresh(preset)
    return preset


@router.delete("/themes/{theme_id}", status_code=204, summary="Удалить тему")
async def delete_theme(theme_id: int, session: Session = Depends(get_session)):
    preset = session.get(ThemePreset, theme_id)
    if not preset:
        raise HTTPException(status_code=404, detail="Тема не найдена")
    session.delete(preset)
    session.commit()
    return None
