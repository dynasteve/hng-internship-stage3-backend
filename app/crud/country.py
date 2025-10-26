from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.database import Base

class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    capital = Column(String(100))
    region = Column(String(100))
    population = Column(Integer, nullable=False)
    currency_code = Column(String(10), nullable=False)
    exchange_rate = Column(Float)
    estimated_gdp = Column(Float)
    flag_url = Column(String(255))
    last_refreshed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
