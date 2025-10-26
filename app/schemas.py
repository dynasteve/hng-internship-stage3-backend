from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==========================
# Base schema
# ==========================
class CountryBase(BaseModel):
    name: str = Field(..., example="France")
    capital: Optional[str] = Field(None, example="Paris")
    region: Optional[str] = Field(None, example="Europe")
    population: Optional[int] = Field(None, example=67000000)
    currency_code: Optional[str] = Field(None, example="EUR")
    exchange_rate: Optional[float] = Field(None, example=1.09)
    estimated_gdp: Optional[float] = Field(None, example=2930000000000)
    flag_url: Optional[str] = Field(None, example="https://flagcdn.com/fr.svg")
    last_refreshed_at: Optional[datetime] = None


# ==========================
# Create schema (for internal use)
# ==========================
class CountryCreate(CountryBase):
    pass


# ==========================
# Response schema
# ==========================
class Country(CountryBase):
    id: int

    class Config:
        from_attributes = True  # replaces orm_mode=True for Pydantic v2


# ==========================
# Status schema (for /countries/status)
# ==========================
class CountryStatus(BaseModel):
    total_countries: int
    last_refreshed_at: Optional[datetime]


# ==========================
# Generic response schemas
# ==========================
class MessageResponse(BaseModel):
    message: str


class RefreshResponse(BaseModel):
    success: bool
    summary_image: Optional[str] = None
