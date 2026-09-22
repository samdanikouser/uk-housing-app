# UK Housing Price Search API

FastAPI service for importing and searching UK Land Registry Price Paid Data for 2024 and 2025.

## Quick start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

For local development without PostgreSQL, remove `.env` and the app uses `sqlite:///./uk_housing.db`. PostgreSQL is the supported deployment database:

```bash
docker compose up -d db
uvicorn app.main:app --reload
```

## Download and import

```bash
python scripts/download_data.py 2024 2025
python scripts/import_data.py data/pp-2024.csv data/pp-2025.csv
```

The importer reads CSV rows incrementally, validates required fields and types, inserts batches of 5,000 rows, and ignores repeated transaction IDs using the database unique key.

## Search

`GET /search` supports `postcode`, `min_price`, `max_price`, `date_from`, `date_to`, `limit`, and `offset`.

```text
/search?postcode=SW1&min_price=200000&max_price=1000000&date_from=2024-01-01&date_to=2025-12-31
```

Example response:

```json
{
	"count": 1,
	"results": [
		{
			"transaction_id": "uuid-example",
			"price": 450000,
			"date_of_transfer": "2025-03-15",
			"postcode": "SW1A 1AA",
			"property_type": "D"
		}
	]
}
```

Postcode searches use an anchored prefix (`SW1%`), so PostgreSQL can use the B-tree postcode index. Price, transfer date, and transaction ID are indexed or constrained for efficient filtering and duplicate prevention.

## Tests

```bash
pytest
```

The API uses parameterized SQLAlchemy expressions, connection health checks, structured request validation, and bounded pagination. Production migrations can be added with Alembic when schema evolution is required; startup table creation keeps this assignment easy to run locally.