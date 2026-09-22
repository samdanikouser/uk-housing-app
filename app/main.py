import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.search import router as search_router
from app.api.upload import router as upload_router
from app.database import engine
from app.models import Base

app = FastAPI(
    title="UK Housing Price API",
    version="1.0.0",
)
app.include_router(search_router)
app.include_router(upload_router)
app.mount("/ui", StaticFiles(directory="app/static", html=True), name="ui")


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    logging.getLogger(__name__).info("Database tables are ready")


@app.get("/")
def health_check():
    return {"message": "UK Housing Price API is running"}