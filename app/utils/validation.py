# app/utils/validation.py
from fastapi import HTTPException

from app.exceptions import ValidationException

def validate_country_data(country):
    errors = {}
    if not country.get("name"):
        errors["name"] = "is required"
    if country.get("population") is None:
        errors["population"] = "is required"
    # currency_code is optional if missing
    if country.get("currency_code") is None:
        country["exchange_rate"] = None
        country["estimated_gdp"] = 0
    if errors:
        raise ValidationException("Validation failed", errors)

