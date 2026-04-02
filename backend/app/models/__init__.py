"""SQLAlchemy models package - register all models here."""

from app.models.base import Base
from app.models.user import User, Role  # noqa: F401
from app.models.product import Product, ProductSKU, ProductImage, Category, Supplier  # noqa: F401
from app.models.material import Material  # noqa: F401
from app.models.order import Order, OrderItem, OrderStatusHistory  # noqa: F401
from app.models.fulfillment import PurchaseOrder, Shipment, Forwarder  # noqa: F401
from app.models.finance import FinanceRecord, ExchangeRate  # noqa: F401
from app.models.customer_service import CSSession, CSMessage, Ticket  # noqa: F401
from app.models.mapping import SKUMapping, MatchRecord  # noqa: F401
from app.models.alert import Alert  # noqa: F401
from app.models.faq import FAQ  # noqa: F401

__all__ = [
    "Base",
    "User", "Role",
    "Product", "ProductSKU", "ProductImage", "Category", "Supplier", "Material",
    "Order", "OrderItem", "OrderStatusHistory",
    "PurchaseOrder", "Shipment", "Forwarder",
    "FinanceRecord", "ExchangeRate",
    "CSSession", "CSMessage", "Ticket",
    "SKUMapping", "MatchRecord",
    "Alert",
    "FAQ",
]
