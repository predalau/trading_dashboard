"""Unified portfolio summary. Mounted at /api/v1/portfolio."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.portfolio_service import build_summary

router = APIRouter()


@router.get("/summary")
async def summary(db: Session = Depends(get_db)):
    return await build_summary(db)
