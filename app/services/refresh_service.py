import random
import httpx
from sqlalchemy.orm import Session
from app import models
from app.utils.image_generator import generate_top5_gdp_image

COUNTRIES_API = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
EXCHANGE_API = "https://open.er-api.com/v6/latest/USD"

async def refresh_country_data(db: Session):
    # Step 1: Fetch countries and exchange rates
    async with httpx.AsyncClient(timeout=30.0) as client:
        countries_resp = await client.get(COUNTRIES_API)
        rates_resp = await client.get(EXCHANGE_API)

    if countries_resp.status_code != 200:
        raise Exception("Failed to fetch data from REST Countries API")
    if rates_resp.status_code != 200:
        raise Exception("Failed to fetch data from Exchange Rate API")

    countries_data = countries_resp.json()
    exchange_data = rates_resp.json().get("rates", {})

    # Step 2: Clear old data
    db.query(models.Country).delete()
    db.commit()

    # Step 3: Insert updated data
    countries = []
    for c in countries_data:
        try:
            population = c.get("population") or 0
            currency_info = c.get("currencies", [{}])[0]
            currency_code = currency_info.get("code") if currency_info else None
            exchange_rate = exchange_data.get(currency_code) if currency_code else None

            if exchange_rate:
                estimated_gdp = (population * random.uniform(1000, 2000)) / exchange_rate
            else:
                estimated_gdp = None

            country = models.Country(
                name=c.get("name"),
                capital=c.get("capital"),
                region=c.get("region"),
                population=population,
                currency_code=currency_code,
                exchange_rate=exchange_rate,
                estimated_gdp=estimated_gdp,
                flag_url=c.get("flag"),
            )
            countries.append(country)
        except Exception as e:
            print("Skipping country due to error:", e)
            continue

    db.bulk_save_objects(countries)
    db.commit()

    # Step 4: Generate image
    top5 = (
        db.query(models.Country)
        .filter(models.Country.estimated_gdp.isnot(None))
        .order_by(models.Country.estimated_gdp.desc())
        .limit(5)
        .all()
    )
    generate_top5_gdp_image(top5)

    print(f"✅ Refreshed {len(countries)} countries.")
    return {"message": f"{len(countries)} countries refreshed successfully."}
