"""
Subscription Management System - Main FastAPI Application
Person 2's modules: Quotations, Subscriptions, Invoices, Payments
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.app.core.config import settings
from backend.app.core.interfaces import initialize_mocks
from backend.app.api.routes import quotations, subscriptions, invoices, payments, products, plans, users, discounts, dashboard

# Initialize mock implementations for Person 1's dependencies
initialize_mocks()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Subscription Management System - Person 2 modules",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Person 2 routers
app.include_router(quotations.router)
app.include_router(subscriptions.router)
app.include_router(invoices.router)
app.include_router(payments.router)
app.include_router(products.router)
app.include_router(plans.router)
app.include_router(users.router)
app.include_router(discounts.router)
app.include_router(dashboard.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}


@app.get("/")
def serve_frontend():
    """Serve the frontend index.html."""
    index_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Subscription Management System API", "docs": "/docs"}


# Mount frontend static files
# main.py is at: backend/app/main.py
# frontend/static is at: frontend/static/
# So from main.py, frontend/static is at ../../frontend/static/
# This allows /static/css/styles.css to map to frontend/static/css/styles.css
static_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "static"))
app.mount("/static", StaticFiles(directory=static_dir), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)