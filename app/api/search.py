from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PropertyTransaction
from app.schemas import SearchResponse

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
def search_transactions(
    postcode: str | None = Query(default=None, min_length=1, max_length=10),
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> SearchResponse:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(status_code=422, detail="min_price must not exceed max_price")
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(status_code=422, detail="date_from must not exceed date_to")

    filters = []
    if postcode:
        filters.append(PropertyTransaction.postcode.like(f"{postcode.strip().upper()}%"))
    if min_price is not None:
        filters.append(PropertyTransaction.price >= min_price)
    if max_price is not None:
        filters.append(PropertyTransaction.price <= max_price)
    if date_from is not None:
        filters.append(PropertyTransaction.date_of_transfer >= date_from)
    if date_to is not None:
        filters.append(PropertyTransaction.date_of_transfer <= date_to)

    base_query: Select = select(PropertyTransaction).where(*filters)
    total = db.scalar(select(func.count()).select_from(base_query.subquery())) or 0
    results = db.scalars(
        base_query.order_by(PropertyTransaction.date_of_transfer.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return SearchResponse(count=total, results=results)