# Country Currency & Exchange API

A RESTful API that fetches country data, caches it in a database, computes estimated GDP, and serves summary data with a generated image.

## Features

- Fetch country data from external APIs
- Compute estimated GDP for each country
- Cache data in a PostgreSQL or MySQL database
- CRUD operations on countries
- Generate a summary image with top 5 GDP countries
- Filter and sort countries

## Endpoints
Method | Endpoint | Description
--- | --- | ---
GET | /countries/refresh  | Fetch countries & exchange rates, update DB, generate summary image
--- | --- | ---
GET | /countries  | Get all countries (optional filters: region, currency; optional sort: gdp_desc, population_asc, etc.)
--- | --- | ---
GET | /countries/{name} | Get a single country by name
--- | --- | ---
DELETE  | /countries/{name} | Delete a country by name
--- | --- | ---
GET | /countries/image  | Serve the summary image (cache/summary.png)
--- | --- | ---
GET | /status |  Show total countries and last refresh timestamp
--- | --- | ---
---

## Setup

### Clone the repo
```bash
git clone https://github.com/yourusername/country-api.git
cd country-api
```

### Create virtual environment & install dependencies
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Set environment variables
Create a .env file:
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/countrydb
```

### Run the server
```bash
uvicorn app.main:app --reload
```

### Access API documentation
Visit http://127.0.0.1:8000/docs

---

## Example Usage

### Refresh countries
GET http://127.0.0.1:8000/countries/refresh

### Get all countries in Africa
GET http://127.0.0.1:8000/countries?region=Africa

### Get summary image
GET http://127.0.0.1:8000/countries/image


## Notes
- Estimated GDP = population × random(1000–2000) ÷ exchange_rate
- If currency or exchange rate is missing, fields may be null or 0
- Summary image is saved at cache/summary.png
- Error responses are JSON:
  - 400: Validation failed
  - 404: Country not found
  - 503: External API unavailable