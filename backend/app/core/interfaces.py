"""
INTEGRATION CONTRACT - Person 1 Dependencies
=============================================
This file defines the interfaces that Person 1 must implement.
Person 2 uses these interfaces with temporary mock implementations
that will be replaced when Person 1 provides their code.

DO NOT MODIFY THE INTERFACE SIGNATURES - they are the contract.
Only the mock implementations in _mock_* functions should be replaced.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session


# =============================================================================
# DATA CLASSES (Contract - do not change)
# =============================================================================

@dataclass
class User:
    """Minimal user info needed by Person 2."""
    id: int
    name: str
    email: str
    role: str  # "admin", "staff", "customer"
    is_active: bool


@dataclass
class Product:
    """Minimal product info needed by Person 2."""
    id: int
    name: str
    type: str
    sales_price: Decimal
    cost_price: Decimal
    notes: Optional[str]


@dataclass
class ProductVariant:
    id: int
    product_id: int
    attribute: str
    value: str
    extra_price: Decimal


@dataclass
class Plan:
    id: int
    name: str
    price: Decimal
    billing_period: str  # "daily", "weekly", "monthly", "yearly"
    min_quantity: int
    available_from: Optional[date]
    available_to: Optional[date]
    auto_close: bool
    allow_early_close: bool
    allow_pause: bool
    allow_renew: bool


@dataclass
class Discount:
    id: int
    name: str
    kind: str  # "fixed" or "percent"
    value: Decimal
    min_purchase: Optional[Decimal]
    min_quantity: Optional[int]
    start_date: Optional[date]
    end_date: Optional[date]
    usage_limit: Optional[int]
    times_used: int
    applies_to: str  # "product" or "subscription"
    product_id: Optional[int]


@dataclass
class Tax:
    id: int
    name: str
    rate_percent: Decimal


@dataclass
class AppliedDiscount:
    """Result from discount calculation."""
    discount_id: int
    name: str
    amount: Decimal


# =============================================================================
# INTERFACES (Contract - do not change signatures)
# =============================================================================

class IAuthService(ABC):
    """Authentication - Person 1 provides."""

    @abstractmethod
    def get_current_user(self, token: str, db: Session) -> User:
        """Validate JWT token and return user."""
        pass

    @abstractmethod
    def require_role(self, *roles: str):
        """FastAPI dependency for role-based access."""
        pass


class IPricingService(ABC):
    """Pricing - Person 1 provides."""

    @abstractmethod
    def unit_price(self, db: Session, product_id: int, variant_id: Optional[int] = None) -> Decimal:
        """Get unit price = sales_price + variant.extra_price."""
        pass


class ITaxService(ABC):
    """Tax calculation - Person 1 provides."""

    @abstractmethod
    def calculate_tax(self, amount: Decimal, tax_id: int, db: Session) -> Decimal:
        """Calculate tax amount for given amount and tax rule."""
        pass


class IDiscountService(ABC):
    """Discount management - Person 1 provides."""

    @abstractmethod
    def find_discounts(
        self,
        db: Session,
        customer_id: int,
        lines: List["SubscriptionLine"],
        subtotal: Decimal,
        on_date: date,
    ) -> List[AppliedDiscount]:
        """Find applicable discounts for given lines and subtotal on a date."""
        pass

    @abstractmethod
    def mark_discount_used(self, db: Session, discount_id: int) -> None:
        """Increment discount usage counter when invoice is confirmed."""
        pass


class IProductRepository(ABC):
    """Product data access - Person 1 provides."""

    @abstractmethod
    def get_product(self, db: Session, product_id: int) -> Optional[Product]:
        pass

    @abstractmethod
    def get_variant(self, db: Session, variant_id: int) -> Optional[ProductVariant]:
        pass

    @abstractmethod
    def list_products(self, db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        pass


class IPlanRepository(ABC):
    """Plan data access - Person 1 provides."""

    @abstractmethod
    def get_plan(self, db: Session, plan_id: int) -> Optional[Plan]:
        pass

    @abstractmethod
    def list_plans(self, db: Session, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[Plan]:
        pass


class IDiscountRepository(ABC):
    """Discount data access - Person 1 provides."""

    @abstractmethod
    def get_active_discounts(self, db: Session, on_date: date) -> List[Discount]:
        pass


class ITaxRepository(ABC):
    """Tax data access - Person 1 provides."""

    @abstractmethod
    def get_tax(self, db: Session, tax_id: int) -> Optional[Tax]:
        pass


class IUserRepository(ABC):
    """User data access - Person 1 provides."""

    @abstractmethod
    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        pass


# =============================================================================
# SERVICE LOCATOR (Initialized at startup with real implementations)
# =============================================================================

class ServiceRegistry:
    """Holds references to Person 1's implementations.

    Person 1 should call register_*() at startup to provide their implementations.
    Until then, mock implementations are used.
    """

    auth: IAuthService = None
    pricing: IPricingService = None
    tax: ITaxService = None
    discount: IDiscountService = None
    product_repo: IProductRepository = None
    plan_repo: IPlanRepository = None
    discount_repo: IDiscountRepository = None
    tax_repo: ITaxRepository = None
    user_repo: IUserRepository = None

    @classmethod
    def register_auth(cls, impl: IAuthService):
        cls.auth = impl

    @classmethod
    def register_pricing(cls, impl: IPricingService):
        cls.pricing = impl

    @classmethod
    def register_tax(cls, impl: ITaxService):
        cls.tax = impl

    @classmethod
    def register_discount(cls, impl: IDiscountService):
        cls.discount = impl

    @classmethod
    def register_product_repo(cls, impl: IProductRepository):
        cls.product_repo = impl

    @classmethod
    def register_plan_repo(cls, impl: IPlanRepository):
        cls.plan_repo = impl

    @classmethod
    def register_discount_repo(cls, impl: IDiscountRepository):
        cls.discount_repo = impl

    @classmethod
    def register_tax_repo(cls, impl: ITaxRepository):
        cls.tax_repo = impl

    @classmethod
    def register_user_repo(cls, impl: IUserRepository):
        cls.user_repo = impl


# =============================================================================
# MOCK IMPLEMENTATIONS (TEMPORARY - replace when Person 1 provides code)
# =============================================================================

class _MockAuthService(IAuthService):
    """TEMP: Mock authentication. REPLACE when Person 1 provides real auth."""

    def get_current_user(self, token: str, db: Session) -> User:
        # TEMP: In real impl, decode JWT and fetch user
        # For testing, return a mock staff user
        return User(
            id=1,
            name="Test Staff",
            email="staff@test.com",
            role="staff",
            is_active=True,
        )

    def require_role(self, *roles: str):
        """TEMP: Return a mock dependency."""
        from fastapi import Depends

        async def _check_role():
            user = self.get_current_user("", None)
            if user.role not in roles:
                from fastapi import HTTPException, status
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required role: {', '.join(roles)}"
                )
            return user
        return Depends(_check_role)


class _MockPricingService(IPricingService):
    """TEMP: Mock pricing. REPLACE when Person 1 provides real pricing."""

    def unit_price(self, db: Session, product_id: int, variant_id: Optional[int] = None) -> Decimal:
        # TEMP: Fetch from DB directly
        from backend.app.models.product import Product, ProductVariant
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product {product_id} not found")

        price = Decimal(str(product.sales_price))
        if variant_id:
            variant = db.query(ProductVariant).filter(
                ProductVariant.id == variant_id,
                ProductVariant.product_id == product_id
            ).first()
            if variant:
                price += Decimal(str(variant.extra_price))
        return price


class _MockTaxService(ITaxService):
    """TEMP: Mock tax. REPLACE when Person 1 provides real tax."""

    def calculate_tax(self, amount: Decimal, tax_id: int, db: Session) -> Decimal:
        from backend.app.models.tax import Tax
        tax = db.query(Tax).filter(Tax.id == tax_id).first()
        if not tax:
            return Decimal("0.00")
        rate = Decimal(str(tax.rate_percent)) / Decimal("100")
        return (amount * rate).quantize(Decimal("0.01"))


class _MockDiscountService(IDiscountService):
    """TEMP: Mock discount. REPLACE when Person 1 provides real discount."""

    def find_discounts(
        self,
        db: Session,
        customer_id: int,
        lines: List["SubscriptionLine"],
        subtotal: Decimal,
        on_date: date,
    ) -> List[AppliedDiscount]:
        from backend.app.models.discount import Discount
        from backend.app.models.subscription import SubscriptionLine

        discounts = db.query(Discount).filter(
            (Discount.start_date.is_(None) | (Discount.start_date <= on_date)),
            (Discount.end_date.is_(None) | (Discount.end_date >= on_date)),
            (Discount.usage_limit.is_(None) | (Discount.times_used < Discount.usage_limit)),
        ).all()

        applied = []
        for discount in discounts:
            if discount.applies_to == "product":
                if discount.product_id:
                    has_product = any(
                        line.product_id == discount.product_id for line in lines
                    )
                    if not has_product:
                        continue

            if discount.min_purchase and subtotal < Decimal(str(discount.min_purchase)):
                continue

            if discount.min_quantity:
                total_qty = sum(line.quantity for line in lines)
                if total_qty < discount.min_quantity:
                    continue

            if discount.kind == "fixed":
                amount = Decimal(str(discount.value))
            elif discount.kind == "percent":
                amount = (subtotal * Decimal(str(discount.value)) / Decimal("100")).quantize(
                    Decimal("0.01")
                )
            else:
                continue

            applied.append(AppliedDiscount(
                discount_id=discount.id,
                name=discount.name,
                amount=amount,
            ))

        return applied

    def mark_discount_used(self, db: Session, discount_id: int) -> None:
        from backend.app.models.discount import Discount
        discount = db.query(Discount).filter(Discount.id == discount_id).first()
        if discount:
            discount.times_used += 1
            db.commit()


class _MockProductRepository(IProductRepository):
    """TEMP: Mock product repo. REPLACE when Person 1 provides real repo."""

    def get_product(self, db: Session, product_id: int) -> Optional[Product]:
        from backend.app.models.product import Product as ProductModel
        p = db.query(ProductModel).filter(ProductModel.id == product_id).first()
        if not p:
            return None
        return Product(
            id=p.id, name=p.name, type=p.type,
            sales_price=Decimal(str(p.sales_price)),
            cost_price=Decimal(str(p.cost_price)),
            notes=p.notes
        )

    def get_variant(self, db: Session, variant_id: int) -> Optional[ProductVariant]:
        from backend.app.models.product import ProductVariant as VariantModel
        v = db.query(VariantModel).filter(VariantModel.id == variant_id).first()
        if not v:
            return None
        return ProductVariant(
            id=v.id, product_id=v.product_id,
            attribute=v.attribute, value=v.value,
            extra_price=Decimal(str(v.extra_price))
        )

    def list_products(self, db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
        from backend.app.models.product import Product as ProductModel
        products = db.query(ProductModel).offset(skip).limit(limit).all()
        return [
            Product(
                id=p.id, name=p.name, type=p.type,
                sales_price=Decimal(str(p.sales_price)),
                cost_price=Decimal(str(p.cost_price)),
                notes=p.notes
            )
            for p in products
        ]


class _MockPlanRepository(IPlanRepository):
    """TEMP: Mock plan repo. REPLACE when Person 1 provides real repo."""

    def get_plan(self, db: Session, plan_id: int) -> Optional[Plan]:
        from backend.app.models.plan import Plan as PlanModel
        p = db.query(PlanModel).filter(PlanModel.id == plan_id).first()
        if not p:
            return None
        return Plan(
            id=p.id, name=p.name, price=Decimal(str(p.price)),
            billing_period=p.billing_period, min_quantity=p.min_quantity,
            available_from=p.available_from, available_to=p.available_to,
            auto_close=p.auto_close, allow_early_close=p.allow_early_close,
            allow_pause=p.allow_pause, allow_renew=p.allow_renew
        )

    def list_plans(self, db: Session, skip: int = 0, limit: int = 100, active_only: bool = False) -> List[Plan]:
        from backend.app.models.plan import Plan as PlanModel
        query = db.query(PlanModel)
        if active_only:
            today = date.today()
            query = query.filter(
                (PlanModel.available_from.is_(None) | (PlanModel.available_from <= today)),
                (PlanModel.available_to.is_(None) | (PlanModel.available_to >= today)),
            )
        plans = query.offset(skip).limit(limit).all()
        return [
            Plan(
                id=p.id, name=p.name, price=Decimal(str(p.price)),
                billing_period=p.billing_period, min_quantity=p.min_quantity,
                available_from=p.available_from, available_to=p.available_to,
                auto_close=p.auto_close, allow_early_close=p.allow_early_close,
                allow_pause=p.allow_pause, allow_renew=p.allow_renew
            )
            for p in plans
        ]


class _MockDiscountRepository(IDiscountRepository):
    """TEMP: Mock discount repo. REPLACE when Person 1 provides real repo."""

    def get_active_discounts(self, db: Session, on_date: date) -> List[Discount]:
        from backend.app.models.discount import Discount as DiscountModel
        discounts = db.query(DiscountModel).filter(
            (DiscountModel.start_date.is_(None) | (DiscountModel.start_date <= on_date)),
            (DiscountModel.end_date.is_(None) | (DiscountModel.end_date >= on_date)),
            (DiscountModel.usage_limit.is_(None) | (DiscountModel.times_used < DiscountModel.usage_limit)),
        ).all()
        return [
            Discount(
                id=d.id, name=d.name, kind=d.kind, value=Decimal(str(d.value)),
                min_purchase=Decimal(str(d.min_purchase)) if d.min_purchase else None,
                min_quantity=d.min_quantity, start_date=d.start_date, end_date=d.end_date,
                usage_limit=d.usage_limit, times_used=d.times_used,
                applies_to=d.applies_to, product_id=d.product_id
            )
            for d in discounts
        ]


class _MockTaxRepository(ITaxRepository):
    """TEMP: Mock tax repo. REPLACE when Person 1 provides real repo."""

    def get_tax(self, db: Session, tax_id: int) -> Optional[Tax]:
        from backend.app.models.tax import Tax as TaxModel
        t = db.query(TaxModel).filter(TaxModel.id == tax_id).first()
        if not t:
            return None
        return Tax(id=t.id, name=t.name, rate_percent=Decimal(str(t.rate_percent)))


class _MockUserRepository(IUserRepository):
    """TEMP: Mock user repo. REPLACE when Person 1 provides real repo."""

    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        from backend.app.models.user import User as UserModel
        u = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not u:
            return None
        return User(id=u.id, name=u.name, email=u.email, role=u.role, is_active=u.is_active)

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        from backend.app.models.user import User as UserModel
        u = db.query(UserModel).filter(UserModel.email == email).first()
        if not u:
            return None
        return User(id=u.id, name=u.name, email=u.email, role=u.role, is_active=u.is_active)


# =============================================================================
# INITIALIZATION - Called at app startup
# =============================================================================

def initialize_mocks():
    """Initialize with mock implementations.

    Person 1 should call their own register_*() functions instead of this
    when their code is ready.
    """
    ServiceRegistry.register_auth(_MockAuthService())
    ServiceRegistry.register_pricing(_MockPricingService())
    ServiceRegistry.register_tax(_MockTaxService())
    ServiceRegistry.register_discount(_MockDiscountService())
    ServiceRegistry.register_product_repo(_MockProductRepository())
    ServiceRegistry.register_plan_repo(_MockPlanRepository())
    ServiceRegistry.register_discount_repo(_MockDiscountRepository())
    ServiceRegistry.register_tax_repo(_MockTaxRepository())
    ServiceRegistry.register_user_repo(_MockUserRepository())


def get_auth() -> IAuthService:
    if ServiceRegistry.auth is None:
        initialize_mocks()
    return ServiceRegistry.auth


def get_pricing() -> IPricingService:
    if ServiceRegistry.pricing is None:
        initialize_mocks()
    return ServiceRegistry.pricing


def get_tax() -> ITaxService:
    if ServiceRegistry.tax is None:
        initialize_mocks()
    return ServiceRegistry.tax


def get_discount() -> IDiscountService:
    if ServiceRegistry.discount is None:
        initialize_mocks()
    return ServiceRegistry.discount


def get_product_repo() -> IProductRepository:
    if ServiceRegistry.product_repo is None:
        initialize_mocks()
    return ServiceRegistry.product_repo


def get_plan_repo() -> IPlanRepository:
    if ServiceRegistry.plan_repo is None:
        initialize_mocks()
    return ServiceRegistry.plan_repo


def get_discount_repo() -> IDiscountRepository:
    if ServiceRegistry.discount_repo is None:
        initialize_mocks()
    return ServiceRegistry.discount_repo


def get_tax_repo() -> ITaxRepository:
    if ServiceRegistry.tax_repo is None:
        initialize_mocks()
    return ServiceRegistry.tax_repo


def get_user_repo() -> IUserRepository:
    if ServiceRegistry.user_repo is None:
        initialize_mocks()
    return ServiceRegistry.user_repo