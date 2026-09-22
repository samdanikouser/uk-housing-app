from datetime import date

from pydantic import BaseModel, ConfigDict


class TransactionResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    transaction_id: str
    price: int
    date_of_transfer: date
    postcode: str
    property_type: str


class SearchResponse(BaseModel):
    count: int
    results: list[TransactionResult]