from datetime import date

import pytest

from app.models import PropertyTransaction


@pytest.fixture(autouse=True)
def seed_transactions(db_session):
    db_session.add_all(
        [
            PropertyTransaction(transaction_id="one", price=450000, date_of_transfer=date(2025, 3, 15), postcode="SW1A 1AA", property_type="D", old_new="N", duration="F", ppd_category="A", record_status="A"),
            PropertyTransaction(transaction_id="two", price=650000, date_of_transfer=date(2024, 8, 10), postcode="SW1A 2BB", property_type="T", old_new="N", duration="L", ppd_category="A", record_status="A"),
        ]
    )
    db_session.commit()


def test_search_filters_by_postcode_price_and_date(client):
    response = client.get("/search", params={"postcode": "sw1", "min_price": 400000, "max_price": 500000, "date_from": "2025-01-01"})
    assert response.status_code == 200
    assert response.json() == {"count": 1, "results": [{"transaction_id": "one", "price": 450000, "date_of_transfer": "2025-03-15", "postcode": "SW1A 1AA", "property_type": "D"}]}


def test_search_rejects_reversed_ranges(client):
    response = client.get("/search", params={"min_price": 500, "max_price": 100})
    assert response.status_code == 422