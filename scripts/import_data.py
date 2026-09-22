import argparse
import logging
from pathlib import Path

from app.database import SessionLocal, engine
from app.models import Base
from app.services.importer import import_csv

logging.basicConfig(level=logging.INFO)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Land Registry price-paid CSV files")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        for path in args.files:
            imported, rejected = import_csv(session, path)
            print(f"{path}: imported={imported}, rejected={rejected}")


if __name__ == "__main__":
    main()