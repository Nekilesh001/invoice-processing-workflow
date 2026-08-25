from fastapi import APIRouter
from app.api.endpoints import invoices, reviews, vendors, purchase_orders, dashboard, auth, analytics

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(invoices.router)
api_router.include_router(reviews.router)
api_router.include_router(vendors.router)
api_router.include_router(purchase_orders.router)
api_router.include_router(analytics.router)

