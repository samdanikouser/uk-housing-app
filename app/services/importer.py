import csv
import logging
from datetime import date
from pathlib import Path
from typing import Iterator

from sqlalchemy import insert
from sqlalchemy.orm import Session

from app.models import PropertyTransaction

logger = logging.getLogger(__name__)
BATCH_SIZE = 5_000
EXPECTED_COLUMNS = 16
MIN_DATE = date(2024, 1, 1)
MAX_DATE = date(2025, 12, 31)


def _parse_row(row: list[str]) -> dict:
    if len(row) != EXPECTED_COLUMNS:
        raise ValueError(f"expected {EXPECTED_COLUMNS} columns, got {len(row)}")
    transaction_id, price, transfer_date, postcode, property_type, old_new, duration, paon, saon, street, locality, town_city, district, county, ppd_category, record_status = row
    transfer_date_value = date.fromisoformat(transfer_date)
    price_value = int(price)
    if not transaction_id or not postcode.strip():
        raise ValueError("transaction_id and postcode are required")
    if price_value <= 0:
        raise ValueError("price must be greater than zero")
    if not MIN_DATE <= transfer_date_value <= MAX_DATE:
        raise ValueError("date_of_transfer must be between 2024-01-01 and 2025-12-31")
    return {
        "transaction_id": transaction_id,
        "price": price_value,
        "date_of_transfer": transfer_date_value,
        "postcode": postcode.strip().upper(),
        "property_type": property_type,
        "old_new": old_new,
        "duration": duration,
        "paon": paon,
        "saon": saon,
        "street": street,
        "locality": locality,
        "town_city": town_city,
        "district": district,
        "county": county,
        "ppd_category": ppd_category,
        "record_status": record_status,
    }


def _valid_rows(path: Path, rejected: list[str]) -> Iterator[dict]:
    with path.open("r", encoding="utf-8", newline="") as csv_file:
        for line_number, row in enumerate(csv.reader(csv_file), start=1):
            try:
                yield _parse_row(row)
            except (TypeError, ValueError) as exc:
                rejected.append(f"line {line_number}: {exc}")


def import_csv(session: Session, path: str | Path, batch_size: int = BATCH_SIZE) -> tuple[int, int]:
    path = Path(path)
    rejected: list[str] = []
    imported = 0
    batch = []
    dialect = session.bind.dialect.name if session.bind is not None else "postgresql"

    for record in _valid_rows(path, rejected):
        batch.append(record)
        if len(batch) >= batch_size:
            imported += _insert_batch(session, batch, dialect)
            batch.clear()
    if batch:
        imported += _insert_batch(session, batch, dialect)
    session.commit()
    logger.info("Imported %s records from %s; rejected %s rows", imported, path, len(rejected))
    return imported, len(rejected)


def _insert_batch(session: Session, batch: list[dict], dialect: str) -> int:
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as dialect_insert
        statement = dialect_insert(PropertyTransaction).values(batch).on_conflict_do_nothing(index_elements=["transaction_id"])
    elif dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as dialect_insert
        statement = dialect_insert(PropertyTransaction).values(batch).on_conflict_do_nothing(index_elements=["transaction_id"])
    else:
        statement = insert(PropertyTransaction).values(batch)
    result = session.execute(statement)
    return result.rowcount or 0