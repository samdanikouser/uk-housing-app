from pathlib import Path

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import PropertyTransaction
from app.services.importer import import_csv


def test_importer_validates_rows_and_skips_duplicates(tmp_path: Path):
    csv_file = tmp_path / "prices.csv"
    row = "id-1,450000,2025-03-15,SW1A 1AA,D,N,F,1,,MAIN ST,,,LONDON,LONDON,A,A"
    csv_file.write_text(f"{row}\n{row}\nid-2,0,2025-03-15,SW1A 1AA,D,N,F,1,,MAIN ST,,,LONDON,LONDON,A,A\nid-3,10,2023-12-31,SW1A 1AA,D,N,F,1,,MAIN ST,,,LONDON,LONDON,A,A\n")

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as session:
        imported, duplicates, rejected, rejected_samples = import_csv(session, csv_file)
        count = session.scalar(select(func.count()).select_from(PropertyTransaction))

    assert (imported, duplicates, rejected, count) == (1, 1, 2, 1)
    assert len(rejected_samples) == 2
    assert "price must be greater than zero" in rejected_samples[0]