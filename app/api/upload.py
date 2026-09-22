import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.importer import import_csv

router = APIRouter()

CHUNK_SIZE = 1024 * 1024  # 1 MB


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="file must be a .csv")

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        while chunk := await file.read(CHUNK_SIZE):
            tmp.write(chunk)

    try:
        imported, duplicates, rejected, rejected_samples = import_csv(db, tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    return {
        "imported": imported,
        "duplicates": duplicates,
        "rejected": rejected,
        "rejected_samples": rejected_samples,
    }
