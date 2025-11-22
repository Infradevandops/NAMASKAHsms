"""Advanced rental schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal


class RentalTemplate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    service_name: str
    country_code: str
    duration_hours: int = Field(default=24, ge=1, le=168)
    auto_renewal: bool = False


class BulkRentalCreate(BaseModel):
    templates: List[RentalTemplate] = Field(..., min_items=1, max_items=10)


class RentalFilter(BaseModel):
    service_name: Optional[str] = None
    country_code: Optional[str] = None
    status: Optional[str] = None
    min_cost: Optional[Decimal] = None
    max_cost: Optional[Decimal] = None
