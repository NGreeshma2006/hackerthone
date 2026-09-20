from pydantic import BaseModel, Field
from typing import Optional, List


class ProductCreate(BaseModel):
    id: str
    name: str
    category: str = "General"
    default_unit: str = "bags"
    minimum_stock: float = 10


class ProductOut(ProductCreate):
    pass


class TransactionCreate(BaseModel):
    product_id: str
    quantity: float
    unit: str
    transaction_type: str
    customer_name: Optional[str] = None
    price: float = 0
    notes: Optional[str] = None
    source: str = "voice"
    language: str = "en"


class VoiceIntent(BaseModel):
    intent: str
    product: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    transaction_type: Optional[str] = None
    notes: Optional[str] = None
    language: str = "en"


class AliasCreate(BaseModel):
    product_id: str
    alias: str
    language: str = "en"


class UnitConversionCreate(BaseModel):
    product_id: str
    from_unit: str
    to_unit: str
    conversion_factor: float


class ReconcileRequest(BaseModel):
    product_id: str
    physical_quantity: float
    unit: str = "bags"
    notes: Optional[str] = None


class LanguageSetting(BaseModel):
    preferred_language: str


class ProductStoryItem(BaseModel):
    product_id: str
    quantity: float
    unit: str
    transaction_type: str
    timestamp: str
    notes: Optional[str] = None


class ProductStory(BaseModel):
    product_id: str
    product_name: str
    current_stock: float
    timeline: List[ProductStoryItem]
    explanation: str
