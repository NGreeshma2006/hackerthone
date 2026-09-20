from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy.orm import Session
from backend.database import Base, engine, get_db, get_mongo_db
from backend.models.models import Product, StockTransaction, ProductAlias, UnitConversion, BusinessSetting
from backend.schemas.schemas import ProductCreate, TransactionCreate, AliasCreate, UnitConversionCreate, ReconcileRequest, LanguageSetting, VoiceIntent
from backend.services.inventory_service import InventoryService
from backend.services.mongo_inventory_service import MongoInventoryService
from backend.services.voice_service import VoiceService
from backend.services.nlp_service import NLPService
import os

from backend.services.auth_service import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="StockStory AI")
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    service = next(get_inventory())
    service.create_default_business()


def get_inventory():
    mongo_db = get_mongo_db()
    if mongo_db is not None:
        yield MongoInventoryService(mongo_db)
        return
    db = next(get_db())
    try:
        yield InventoryService(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "StockStory AI is running"}


@app.get("/db-status")
def db_status():
    mongo_db = get_mongo_db()
    return {
        "database": "mongodb" if mongo_db is not None else "sqlite",
        "mongo_configured": mongo_db is not None,
        "message": "MongoDB connected" if mongo_db is not None else "SQLite fallback active"
    }


@app.get("/products")
def get_products(inventory = Depends(get_inventory)):
    products = inventory.get_products()
    return [
        {
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "default_unit": product.default_unit,
            "minimum_stock": product.minimum_stock,
            "current_stock": inventory.current_stock_for_product(product.id),
        }
        for product in products
    ]


@app.post("/products")
def create_product(product: ProductCreate, inventory = Depends(get_inventory)):
    record = Product(id=product.id, name=product.name, category=product.category, default_unit=product.default_unit, minimum_stock=product.minimum_stock)
    return inventory.upsert_product(record)


@app.get("/products/{id}")
def get_product(id: str, inventory = Depends(get_inventory)):
    product = inventory.get_product(id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.get("/products/{id}/story")
def product_story(id: str, inventory = Depends(get_inventory)):
    story = inventory.get_product_story(id)
    return story


@app.post("/transactions")
def create_transaction(transaction: TransactionCreate, inventory = Depends(get_inventory)):
    return inventory.create_transaction(
        product_id=transaction.product_id,
        quantity=transaction.quantity,
        unit=transaction.unit,
        transaction_type=transaction.transaction_type,
        customer_name=transaction.customer_name,
        price=transaction.price,
        notes=transaction.notes,
        source=transaction.source,
        language=transaction.language,
    )


@app.get("/activity")
def activity(inventory = Depends(get_inventory)):
    # Keeps direct service calls used by the existing test suite compatible.
    if hasattr(inventory, 'query'):
        inventory = InventoryService(inventory)
    return inventory.activity()


class VoiceRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    language: Literal['en', 'hi', 'te', 'ta', 'kn', 'ml', 'mr', 'bn'] = 'en'


@app.post('/voice/speak')
async def speak_voice(payload: VoiceRequest):
    from backend.services.speech_service import synthesize
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail='No speech text supplied')
    try:
        audio = await synthesize(payload.text.strip(), payload.language)
    except Exception:
        raise HTTPException(status_code=503, detail='Speech playback is temporarily unavailable')
    return Response(audio, media_type='audio/mpeg', headers={'Cache-Control': 'no-store'})


@app.post("/voice/process")
def process_voice(payload: VoiceRequest, inventory = Depends(get_inventory)):
    text = payload.text.strip()
    language = payload.language
    if not text:
        raise HTTPException(status_code=400, detail="No speech text supplied")
    service = VoiceService(inventory)
    return service.process_voice(text, language)


@app.post("/stock/reconcile")
def reconcile_stock(payload: ReconcileRequest, inventory = Depends(get_inventory)):
    return inventory.reconcile_stock(payload.product_id, payload.physical_quantity, payload.unit, payload.notes)


@app.get("/alerts")
def alerts(inventory = Depends(get_inventory)):
    return inventory.get_alerts()


@app.get("/insights")
def insights(inventory = Depends(get_inventory)):
    return inventory.get_insights()


@app.post("/aliases")
def add_alias(alias: AliasCreate, inventory = Depends(get_inventory)):
    return inventory.add_alias(alias.product_id, alias.alias, alias.language)


@app.get("/languages")
def languages():
    from backend.services.language_service import SUPPORTED_LANGUAGES
    return {"languages": SUPPORTED_LANGUAGES}


@app.post("/language")
def set_language(setting: LanguageSetting, db: Session = Depends(get_db)):
    business = db.query(BusinessSetting).first()
    if not business:
        business = BusinessSetting()
        db.add(business)
    business.preferred_language = setting.preferred_language
    db.commit()
    return business


@app.post("/unit-conversions")
def add_unit_conversion(conversion: UnitConversionCreate, inventory = Depends(get_inventory)):
    return inventory.add_unit_conversion(conversion.product_id, conversion.from_unit, conversion.to_unit, conversion.conversion_factor)
