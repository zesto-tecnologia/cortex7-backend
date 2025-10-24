"""
Pydantic schemas for Ordens de Compra (Purchase Orders).
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class PurchaseOrderItem(BaseModel):
    """Schema for purchase order item."""

    description: str = Field(..., min_length=1, max_length=500)
    quantity: int = Field(..., ge=1)
    unit_amount: float = Field(..., gt=0)
    unit: Optional[str] = Field(None, max_length=10)  # UN, KG, L, etc.
    observations: Optional[str] = None


class PurchaseOrderBase(BaseModel):
    """Base schema for Purchase Order."""

    company_id: UUID
    requester_id: UUID
    supplier_id: UUID
    cost_center: Optional[str] = Field(None, max_length=50)
    expected_delivery_date: Optional[date] = None
    metadata: Optional[Dict[str, Any]] = None


class PurchaseOrderCreate(PurchaseOrderBase):
    """Schema for creating a Purchase Order."""

    items: List[PurchaseOrderItem] = Field(..., min_items=1)
    status: str = Field(default="draft", max_length=30)

    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('Purchase order must have at least one item')
        return v


class PurchaseOrderUpdate(BaseModel):
    """Schema for updating a Purchase Order."""

    supplier_id: Optional[UUID] = None
    items: Optional[List[PurchaseOrderItem]] = None
    cost_center: Optional[str] = Field(None, max_length=50)
    expected_delivery_date: Optional[date] = None
    metadata: Optional[Dict[str, Any]] = None


class PurchaseOrderResponse(PurchaseOrderBase):
    """Schema for Purchase Order response."""

    id: UUID
    number: str
    status: str
    items: List[Dict[str, Any]]
    approvers: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PurchaseOrderWithApprovals(PurchaseOrderResponse):
    """Purchase Order with approval details."""

    requester: Optional["UserResponse"] = None
    supplier: Optional["SupplierResponse"] = None

    class Config:
        from_attributes = True


# Import after class definition to avoid circular imports
from services.financial.schemas.supplier import SupplierResponse
from services.hr.schemas.user import UserResponse

PurchaseOrderWithApprovals.model_rebuild()