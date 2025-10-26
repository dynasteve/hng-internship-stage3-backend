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

router = APIRouter(prefix="/countries", tags=["Countries"])


# ✅ 1. Serve the generated image — must come FIRST
@router.get(
    "/image",
    response_class=FileResponse,
    summary="Get the generated top 5 GDP countries image",
)
def get_summary_image():
    # Use absolute path from project root (not app/)
    image_path = os.path.join(os.getcwd(), "top5_gdp.png")
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Summary image not found")
    return FileResponse(image_path, media_type="image/png")


# ✅ 2. Refresh and cache countries
@router.get("/refresh", response_model=schemas.RefreshResponse)
async def refresh_countries(db: Session = Depends(get_db)):
    # 1️⃣ Fetch country data
    countries_url = "https://restcountries.com/v2/all?fields=name,capital,region,population,currencies,flag"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(countries_url)
            if response.status_code != 200:
                raise ExternalAPIException("Could not fetch data from Countries API")
            countries_data = response.json()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "External data source unavailable", "details": str(e)},
        )

    # 2️⃣ Fetch exchange rates
    exchange_url = "https://open.er-api.com/v6/latest/USD"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(exchange_url)
            if response.status_code != 200:
                raise ExternalAPIException("Could not fetch data from Exchange API")
            exchange_data = response.json()
            rates = exchange_data.get("rates", {})
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={"error": "External data source unavailable", "details": str(e)},
        )

    # 3️⃣ Process countries
    processed_countries = []
    for c in countries_data:
        country = {
            "name": c.get("name"),
            "capital": c.get("capital"),
            "region": c.get("region"),
            "population": c.get("population"),
            "flag_url": c.get("flag"),
        }

        currencies = c.get("currencies", [])
        if currencies:
            currency_code = currencies[0].get("code")
            country["currency_code"] = currency_code
            exchange_rate = rates.get(currency_code)
            country["exchange_rate"] = exchange_rate if exchange_rate else None
            country["estimated_gdp"] = (
                country["population"] * random.randint(1000, 2000) / exchange_rate
                if exchange_rate else None
            )
        else:
            country["currency_code"] = None
            country["exchange_rate"] = None
            country["estimated_gdp"] = 0

        # Validate required fields
        try:
            validate_country_data(country)
        except ValidationException as ve:
            raise HTTPException(status_code=400, detail={"error": "Validation failed", "details": ve.errors})

        processed_countries.append(country)

    # 4️⃣ Upsert into DB
    for country in processed_countries:
        existing = crud.get_country_by_name(db, country["name"])
        if existing:
            for k, v in country.items():
                setattr(existing, k, v)
            existing.last_refreshed_at = datetime.utcnow()
        else:
            new_country = crud.create_country_obj(country)
            new_country.last_refreshed_at = datetime.utcnow()
            db.add(new_country)

    db.commit()

    # 5️⃣ Generate summary image
    image_path = crud.generate_summary_image(db)

    return {"success": True, "summary_image": image_path}

# ✅ 3. Get all countries (with filters + sorting)
@router.get(
    "",
    response_model=List[schemas.Country],
    summary="Get all countries with optional filters and sorting",
)
def get_countries(
    db: Session = Depends(get_db),
    region: Optional[str] = Query(None, description="Filter by region name (case-insensitive)"),
    currency: Optional[str] = Query(None, description="Filter by currency code (case-insensitive)"),
    sort: Optional[str] = Query(
        None,
        description="Sort by GDP or population (e.g. 'gdp_desc', 'gdp_asc', 'population_desc', 'population_asc')",
    ),
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


# ✅ 4. Status endpoint
@router.get(
    "/status",
    response_model=schemas.CountryStatus,
    summary="Get total countries and last refresh timestamp",
)
def get_status(db: Session = Depends(get_db)):
    total = db.query(models.Country).count()
    last = db.query(func.max(models.Country.last_refreshed_at)).scalar()
    return {
        "total_countries": total,
        "last_refreshed_at": last,
    }


# ✅ 5. Get a single country by name
@router.get(
    "/{name}",
    response_model=schemas.Country,
    summary="Get details of a single country by name",
)
def get_country(name: str, db: Session = Depends(get_db)):
    country = crud.get_country_by_name(db, name=name)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country '{name}' not found")
    return country


# ✅ 6. Delete a country by name
@router.delete(
    "/{name}",
    response_model=schemas.MessageResponse,
    summary="Delete a country by name",
)
def delete_country(name: str, db: Session = Depends(get_db)):
    country = db.query(models.Country).filter(func.lower(models.Country.name) == name.lower()).first()
    if not country:
        raise HTTPException(status_code=404, detail={"error": "Country not found"})
    db.delete(country)
    db.commit()
    return {"message": f"Country '{name}' deleted successfully."}
