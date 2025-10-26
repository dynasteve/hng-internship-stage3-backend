from fastapi import FastAPI
from app.database import init_db
from app.routes import countries

app = FastAPI(title="Country Currency & Exchange API")

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(countries.router)

@app.get("/")
def root():
    return {"message": "Country API running successfully 🚀"}
