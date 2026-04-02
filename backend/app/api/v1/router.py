"""API v1 router aggregation."""

from fastapi import APIRouter

api_router = APIRouter()

# Register module routers
from app.api.v1.auth import router as auth_router
from app.api.v1.products import router as products_router
from app.api.v1.orders import router as orders_router
from app.api.v1.materials import router as materials_router
from app.api.v1.modules import (
    pricing_router,
    listing_router,
    fulfillment_router,
    finance_router,
)
from app.api.v1.customer_service import router as customer_service_router

api_router.include_router(auth_router)
api_router.include_router(products_router)
api_router.include_router(orders_router)
api_router.include_router(materials_router)
api_router.include_router(pricing_router)
api_router.include_router(listing_router)
api_router.include_router(fulfillment_router)
api_router.include_router(customer_service_router, prefix="/v1/customer-service", tags=["CustomerService"])
api_router.include_router(finance_router)
