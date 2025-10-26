from fastapi import FastAPI
from app.database import init_db
from app.routes import countries

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict
import os
import random
import httpx
from datetime import datetime

from app.deps import get_db
from app import crud, models, schemas
from app.exceptions import NotFoundException, ValidationException, ExternalAPIException
from app.utils.validation import validate_country_data

app = FastAPI(title="Country Currency & Exchange API")

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(countries.router)

@app.get("/")
def root():
    return {"message": "Country API running successfully 🚀"}

@app.get(
    "/status",
    response_model=schemas.CountryStatus,
    summary="Get total countries and last refresh timestamp"
)
def get_status(db: Session = Depends(get_db)) -> Dict:
    total = db.query(func.count(models.Country.id)).scalar()
    last = db.query(func.max(models.Country.last_refreshed_at)).scalar()

    return {
        "total_countries": total,
        "last_refreshed_at": last
    }