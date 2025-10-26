from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
from app.deps import get_db
from app import models
from app.services.refresh_service import refresh_country_data

router = APIRouter(prefix="/countries", tags=["Countries"])

# ✅ 1. Refresh and cache countries
@router.get("/refresh")
async def refresh_countries(db: Session = Depends(get_db)):
    try:
        result = await refresh_country_data(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ✅ 2. Get all countries (with filters + sorting)
@router.get("")
def get_countries(
    db: Session = Depends(get_db),
    region: str = Query(None),
    currency: str = Query(None),
    sort: str = Query(None)
):
    query = db.query(models.Country)

    if region:
        query = query.filter(func.lower(models.Country.region) == region.lower())
    if currency:
        query = query.filter(func.lower(models.Country.currency_code) == currency.lower())

    if sort:
        if sort == "gdp_desc":
            query = query.order_by(models.Country.estimated_gdp.desc())
        elif sort == "gdp_asc":
            query = query.order_by(models.Country.estimated_gdp.asc())
        elif sort == "population_desc":
            query = query.order_by(models.Country.population.desc())
        elif sort == "population_asc":
            query = query.order_by(models.Country.population.asc())

    countries = query.all()
    return countries


# ✅ 3. Get a single country by name
@router.get("/{name}")
def get_country(name: str, db: Session = Depends(get_db)):
    country = db.query(models.Country).filter(func.lower(models.Country.name) == name.lower()).first()
    if not country:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    return country


# ✅ 4. Delete a country by name
@router.delete("/{name}")
def delete_country(name: str, db: Session = Depends(get_db)):
    country = db.query(models.Country).filter(func.lower(models.Country.name) == name.lower()).first()
    if not country:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    db.delete(country)
    db.commit()
    return {"message": f"Country '{name}' deleted successfully."}


# ✅ 5. Status endpoint
@router.get("/status")
def get_status(db: Session = Depends(get_db)):
    total = db.query(models.Country).count()
    last = db.query(func.max(models.Country.last_refreshed_at)).scalar()
    return {
        "total_countries": total,
        "last_refreshed_at": last
    }


# ✅ 6. Serve the generated image
@router.get("/image")
def get_summary_image():
    image_path = "top5_gdp.png"
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail={"error": "Summary image not found"})
    return FileResponse(image_path, media_type="image/png")
