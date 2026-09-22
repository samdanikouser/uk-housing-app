from datetime import date
from sqlalchemy import Date, Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PropertyTransaction(Base):
    __tablename__ = "property_transactions"

    transaction_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    price: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    date_of_transfer: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    postcode: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    property_type: Mapped[str] = mapped_column(String(1), nullable=False)
    old_new: Mapped[str] = mapped_column(String(1), nullable=False)
    duration: Mapped[str] = mapped_column(String(1), nullable=False)
    paon: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    saon: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    street: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    locality: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    town_city: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    district: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    county: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    ppd_category: Mapped[str] = mapped_column(String(1), nullable=False)
    record_status: Mapped[str] = mapped_column(String(1), nullable=False)

    __table_args__ = (
        Index("ix_property_transactions_postcode", "postcode"),
        Index("ix_property_transactions_price", "price"),
        Index("ix_property_transactions_date", "date_of_transfer"),
        Index("ix_property_transactions_search", "postcode", "date_of_transfer", "price"),
    )