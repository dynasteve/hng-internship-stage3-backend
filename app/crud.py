import random
import httpx
import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app import models
from app.exceptions import ExternalAPIException
from PIL import Image, ImageDraw, ImageFont

# -------------------------------
# Refresh countries and update DB
# -------------------------------
def refresh_countries(db: Session, countries_data: list):
    # Get exchange rates
    try:
        exchange_resp = httpx.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        if exchange_resp.status_code != 200:
            raise ExternalAPIException("Failed to fetch exchange rates")
        exchange_data = exchange_resp.json().get("rates", {})
    except Exception as e:
        raise ExternalAPIException(str(e))

    # Loop through all countries
    for country in countries_data:
        name = country.get("name", {}).get("common") or country.get("name")
        capital = country.get("capital", [None])[0] if isinstance(country.get("capital"), list) else country.get("capital")
        region = country.get("region")
        population = country.get("population", 0)
        flag_url = country.get("flags", {}).get("png") or country.get("flag")

        # Handle currencies safely
        currencies = country.get("currencies", {})
        currency_code = None
        if isinstance(currencies, dict):
            keys = list(currencies.keys())
            if keys:
                currency_code = keys[0]

        # Get exchange rate and compute GDP
        exchange_rate = exchange_data.get(currency_code)
        estimated_gdp = None
        if exchange_rate and exchange_rate > 0:
            multiplier = random.uniform(1000, 2000)
            estimated_gdp = (population * multiplier) / exchange_rate
        else:
            estimated_gdp = 0

        # Check if exists
        existing = db.query(models.Country).filter(func.lower(models.Country.name) == name.lower()).first()
        if existing:
            # Update
            existing.capital = capital
            existing.region = region
            existing.population = population
            existing.currency_code = currency_code
            existing.exchange_rate = exchange_rate
            existing.estimated_gdp = estimated_gdp
            existing.flag_url = flag_url
            existing.last_refreshed_at = datetime.utcnow()
        else:
            # Insert
            new_country = models.Country(
                name=name,
                capital=capital,
                region=region,
                population=population,
                currency_code=currency_code,
                exchange_rate=exchange_rate,
                estimated_gdp=estimated_gdp,
                flag_url=flag_url,
                last_refreshed_at=datetime.utcnow(),
            )
            db.add(new_country)

    db.commit()


# -------------------------------
# Generate summary image
# -------------------------------
def generate_summary_image(db: Session):
    countries = db.query(models.Country).order_by(models.Country.estimated_gdp.desc()).limit(5).all()
    total = db.query(models.Country).count()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    img = Image.new("RGB", (600, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    title = f"Countries Summary ({timestamp})"
    draw.text((10, 10), title, fill=(0, 0, 0))
    draw.text((10, 40), f"Total Countries: {total}", fill=(0, 0, 0))
    draw.text((10, 70), "Top 5 by Estimated GDP:", fill=(0, 0, 0))

    y = 100
    for i, c in enumerate(countries, start=1):
        gdp_text = f"{c.estimated_gdp:,.2f}" if c.estimated_gdp else "N/A"
        draw.text((20, y), f"{i}. {c.name} - {gdp_text}", fill=(0, 0, 0))
        y += 25

    # ✅ Always save in app root
    output_path = os.path.join(os.path.dirname(__file__), "..", "top5_gdp.png")
    output_path = os.path.abspath(output_path)

    img.save(output_path)
    return output_path

def get_country_by_name(db: Session, name: str):
    return (
        db.query(models.Country)
        .filter(func.lower(models.Country.name) == name.lower())
        .first()
    )