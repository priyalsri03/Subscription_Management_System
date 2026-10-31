# Person 1's models (shared)
from backend.app.models.user import User
from backend.app.models.product import Product, ProductVariant
from backend.app.models.plan import Plan
from backend.app.models.discount import Discount
from backend.app.models.tax import Tax

# Person 2's models
from backend.app.models.quotation import QuotationTemplate, QuotationTemplateLine
from backend.app.models.subscription import Subscription, SubscriptionLine
from backend.app.models.invoice import Invoice, InvoiceLine
from backend.app.models.payment import Payment

__all__ = [
    # Person 1
    "User",
    "Product",
    "ProductVariant",
    "Plan",
    "Discount",
    "Tax",
    # Person 2
    "QuotationTemplate",
    "QuotationTemplateLine",
    "Subscription",
    "SubscriptionLine",
    "Invoice",
    "InvoiceLine",
    "Payment",
]