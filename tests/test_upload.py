from sqlalchemy import func, select

from app.models import PropertyTransaction


def test_upload_imports_valid_rows_and_skips_duplicates(client, db_session):
    row = "id-1,450000,2025-03-15,SW1A 1AA,D,N,F,1,,MAIN ST,,,LONDON,LONDON,A,A"
    csv_content = f"{row}\n{row}\n"

    response = client.post(
        "/upload",
        files={"file": ("prices.csv", csv_content, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json() == {"imported": 1, "duplicates": 1, "rejected": 0, "rejected_samples": []}

    count = db_session.scalar(select(func.count()).select_from(PropertyTransaction))
    assert count == 1


def test_upload_rejects_non_csv_file(client):
    response = client.post(
        "/upload",
        files={"file": ("prices.txt", "not a csv", "text/plain")},
    )
    assert response.status_code == 422
