from sqlalchemy.orm import Session
from backend.services.inventory_service import InventoryService


class StockStoryService:
    def __init__(self, db: Session):
        self.db = db
        self.inventory = InventoryService(db)

    def explain_product(self, product_id: str):
        return self.inventory.get_product_story(product_id)

    def explain_where_stock_went(self, product_id: str):
        story = self.inventory.get_product_story(product_id)
        return story["explanation"]
