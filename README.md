# UK Housing Price Search

FastAPI service for importing and searching UK Land Registry Price Paid Data (2024–2025), with a built-in web UI at `/ui/` for uploading CSVs and searching without touching the API directly.

![Search bar with postcode, price range slider, and date range picker](docs/screenshots/search-bar.webp)

![Search results as property cards](docs/screenshots/results-cards.webp)

## Quick start

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/ui/` for the web UI. Interactive API docs are available at:

- `http://127.0.0.1:8000/docs` — Swagger UI (interactive, "Try it out" buttons)
- `http://127.0.0.1:8000/redoc` — ReDoc (read-only, cleaner reference view)

![Swagger UI at /docs](docs/screenshots/swagger-docs.webp)

![ReDoc at /redoc](docs/screenshots/redoc.webp)

For local development without PostgreSQL, remove/rename `.env` (or `unset DATABASE_URL` if it's exported in your shell) and the app falls back to `sqlite:///./uk_housing.db`. PostgreSQL is the supported deployment database:

```bash
docker compose up -d db
uvicorn app.main:app --reload
```

`.env.example` has the matching connection string (`postgresql+psycopg://postgres:postgres@localhost:5432/uk_housing`). If port 5432 is already taken by something else on your machine, `docker compose up` will fail with "port is already allocated" — that's a different Postgres instance, not this project's container.

## Getting the data

```bash
python scripts/download_data.py 2024 2025
```

Downloads the official CSVs from the Land Registry into `data/`. Each file is large (~150–200MB, ~900k+ rows).

## Importing data

Two ways in:

**CLI** (for bulk/scripted imports):
```bash
python scripts/import_data.py data/pp-2024.csv data/pp-2025.csv
```

**Web UI**: go to `/ui/`, click **Upload CSV** (opens the file picker directly — no separate "choose file" step), pick a CSV. Shows a live upload progress bar, then an indeterminate "Processing…" indicator while the server parses and inserts.

Both paths call the same importer, which:
- Streams the CSV row by row (doesn't load the whole file into memory)
- Validates each row: correct column count (16), valid date, `price > 0`, `transaction_id` and `postcode` both present
- Batches inserts (5,000 rows at a time), committing after each batch
- Uses `ON CONFLICT (transaction_id) DO NOTHING` to skip rows already in the database — safe to re-run the same file, or an overlapping file, any number of times

The response (both CLI output and the UI message) reports three numbers:
- **imported** — genuinely new rows inserted
- **duplicates** — rows that were valid but already existed (transaction_id already in the DB)
- **rejected** — rows that failed validation, plus a small sample of the actual reasons (e.g. `"line 603: transaction_id and postcode are required"`)

In the real HM Land Registry files, essentially all rejections are rows with a blank postcode (new-build/off-plan sales registered before an address is assigned) — that's genuine source-data incompleteness, not an import bug.

### CSV column reference

The Land Registry files have no header row. Column order:

| # | Column | Meaning | DB field |
|---|---|---|---|
| 1 | Transaction ID | Unique GUID | `transaction_id` |
| 2 | Price | Sale price | `price` |
| 3 | Date of Transfer | Completion date (format `YYYY-MM-DD HH:MM`) | `date_of_transfer` |
| 4 | Postcode | Can be blank | `postcode` |
| 5 | Property Type | `D`=Detached, `S`=Semi-Detached, `T`=Terraced, `F`=Flat/Maisonette, `O`=Other | `property_type` |
| 6 | Old/New | `Y`=new build, `N`=established | `old_new` |
| 7 | Duration | `F`=Freehold, `L`=Leasehold | `duration` |
| 8 | PAON | House number/name | `paon` |
| 9 | SAON | Flat/unit number | `saon` |
| 10 | Street | | `street` |
| 11 | Locality | | `locality` |
| 12 | Town/City | | `town_city` |
| 13 | District | | `district` |
| 14 | County | | `county` |
| 15 | PPD Category Type | `A`=standard, `B`=additional (repossessions etc.) | `ppd_category` |
| 16 | Record Status | `A`/`C`/`D` (monthly files only) | `record_status` |

## Search

### Web UI

`/ui/` gives you:
- A postcode field
- A **drag-handle price range slider** (£0–£2,000,000, no external dependency — two overlaid native range inputs)
- A **single date-range picker** ("Sold between") — click once, pick a start and end date in the same calendar (powered by [flatpickr](https://flatpickr.js.org), loaded via CDN, no build step), same interaction pattern as booking sites
- Results as property cards (price, type/tenure badges, address, sold date) with Prev/Next pagination

### API

`GET /search` — query params:

| Param | Type | Notes |
|---|---|---|
| `postcode` | string | Prefix match (`SW1` matches `SW1A 1AA`, `SW1A 2BB`, ...) |
| `min_price` | int | |
| `max_price` | int | |
| `date_from` | date (`YYYY-MM-DD`) | |
| `date_to` | date (`YYYY-MM-DD`) | |
| `limit` | int, default 100, max 1000 | |
| `offset` | int, default 0 | |

```text
GET /search?postcode=SW1&min_price=200000&max_price=1000000&date_from=2024-01-01&date_to=2025-12-31&limit=50&offset=0
```

Example response:

```json
{
  "count": 1,
  "results": [
    {
      "transaction_id": "{42C129E4-C259-60A9-E063-4804A8C0C25D}",
      "price": 450000,
      "date_of_transfer": "2025-03-15",
      "postcode": "SW1A 1AA",
      "property_type": "D",
      "duration": "F",
      "street": "MAIN ST",
      "town_city": "LONDON"
    }
  ]
}
```

`count` is the total number of matches (for pagination), not just the length of `results`.

### Search efficiency

- `postcode` uses an anchored prefix (`LIKE 'SW1%'`), which can use the B-tree index rather than a full scan
- Indexes on `postcode`, `price`, `date_of_transfer` individually, plus a composite `(postcode, date_of_transfer, price)` index covering the most common combined filter
- `transaction_id` is the primary key, enforcing uniqueness and giving duplicate-safe imports for free
- Pagination is bounded (`limit` capped at 1000) so a single request can't pull unbounded result sets

## Upload endpoint

`POST /upload` — multipart form with a `file` field (must end in `.csv`). Streams the upload to a temp file in 1MB chunks (doesn't buffer the whole file in memory), then imports it.

```json
{
  "imported": 927813,
  "duplicates": 0,
  "rejected": 2746,
  "rejected_samples": ["line 603: transaction_id and postcode are required", "..."]
}
```

## Tests

```bash
pytest
```

Covers CSV parsing/validation, duplicate handling (both within a single file and across repeated uploads), the `/search` endpoint's filters and validation, and the `/upload` endpoint.

## Notes

- The API uses parameterized SQLAlchemy expressions (no string-built SQL), connection health checks (`pool_pre_ping`), and structured request validation via FastAPI/Pydantic.
- Logging is configured at the app level (`logging.basicConfig`), so import progress (`Imported N records...`) is visible in server logs, not just when running the CLI script.
- Table creation happens on startup (`Base.metadata.create_all`) rather than via migrations — fine for this project's scope; add Alembic if the schema needs to evolve under real data.
- The frontend (`app/static/index.html`) is plain HTML/CSS/JS — no build step, no framework. The only external dependencies are two small CDN-loaded libraries for UI polish: flatpickr (date range picker) and Google Fonts (Josefin Sans/Inter). Everything else is dependency-free.
