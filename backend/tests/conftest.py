"""
Test fixtures for Person 2 modules.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.db import Base, get_db
from backend.app.core.interfaces import (
    ServiceRegistry, IAuthService, User
)
from backend.app.main import app

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Global db session for tests
_test_db_session = None


def _get_test_db():
    global _test_db_session
    if _test_db_session is None:
        _test_db_session = TestingSessionLocal()
    return _test_db_session


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    global _test_db_session
    Base.metadata.create_all(bind=engine)
    _test_db_session = TestingSessionLocal()
    yield _test_db_session
    _test_db_session.close()
    Base.metadata.drop_all(bind=engine)
    _test_db_session = None


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with a fresh database."""
    # Override get_db dependency
    def get_test_db():
        return db

    app.dependency_overrides[get_db] = get_test_db

    # Initialize mocks
    from backend.app.core.interfaces import initialize_mocks
    initialize_mocks()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth(db):
    """Mock authentication to return a staff user for testing."""
    class MockAuthService(IAuthService):
        def get_current_user(self, token: str, db_session):
            return User(
                id=1,
                name="Test Staff",
                email="staff@test.com",
                role="staff",
                is_active=True,
            )

        def require_role(self, *roles: str):
            from fastapi import Depends as FastDeps
            from fastapi import HTTPException, status

            async def _check_role():
                user = self.get_current_user("", db)
                if user.role not in roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Required role: {', '.join(roles)}"
                    )
                return user
            return FastDeps(_check_role)

    ServiceRegistry.register_auth(MockAuthService())
    return ServiceRegistry.auth


@pytest.fixture
def sample_data(db):
    """Create sample data for tests."""
    from datetime import date
    from decimal import Decimal
    from backend.app.models.user import User as UserModel
    from backend.app.models.product import Product as ProductModel, ProductVariant as VariantModel
    from backend.app.models.plan import Plan as PlanModel
    from backend.app.models.discount import Discount as DiscountModel
    from backend.app.models.tax import Tax as TaxModel
    from backend.app.models.quotation import QuotationTemplate as TemplateModel
    from backend.app.models.quotation import QuotationTemplateLine as TplLineModel

    # Create users
    admin = UserModel(name="Admin", email="admin@test.com", password_hash="hash", role="admin", is_active=True)
    staff = UserModel(name="Staff", email="staff@test.com", password_hash="hash", role="staff", is_active=True)
    customer = UserModel(name="Customer", email="customer@test.com", password_hash="hash", role="customer", is_active=True)
    db.add_all([admin, staff, customer])
    db.flush()

    # Create products
    product1 = ProductModel(name="Pro", type="software", sales_price=Decimal("1000.00"), cost_price=Decimal("500.00"), notes="Professional plan")
    product2 = ProductModel(name="Basic", type="software", sales_price=Decimal("500.00"), cost_price=Decimal("200.00"), notes="Basic plan")
    db.add_all([product1, product2])
    db.flush()

    # Create variants
    variant1 = VariantModel(product_id=product1.id, attribute="brand", value="Odoo", extra_price=Decimal("560.00"))
    db.add(variant1)
    db.flush()

    # Create plans with allow_pause=True
    plan1 = PlanModel(name="Monthly Pro", price=Decimal("1000.00"), billing_period="monthly", min_quantity=1, allow_pause=True)
    plan2 = PlanModel(name="Yearly Pro", price=Decimal("10000.00"), billing_period="yearly", min_quantity=1, allow_pause=True)
    db.add_all([plan1, plan2])
    db.flush()

    # Create discounts
    discount1 = DiscountModel(name="Bulk Discount", kind="percent", value=Decimal("10.00"), min_quantity=5, applies_to="subscription")
    db.add(discount1)
    db.flush()

    # Create taxes
    tax1 = TaxModel(name="GST", rate_percent=Decimal("18.00"))
    db.add(tax1)
    db.flush()

    # Create quotation template
    template = TemplateModel(name="Enterprise Template", plan_id=plan1.id, validity_days=30)
    db.add(template)
    db.flush()

    # Add template lines
    tpl_line1 = TplLineModel(template_id=template.id, product_id=product1.id, quantity=1)
    tpl_line2 = TplLineModel(template_id=template.id, product_id=product2.id, quantity=2)
    db.add_all([tpl_line1, tpl_line2])
    db.commit()

    return {
        "admin": admin,
        "staff": staff,
        "customer": customer,
        "product1": product1,
        "product2": product2,
        "variant1": variant1,
        "plan1": plan1,
        "plan2": plan2,
        "discount1": discount1,
        "tax1": tax1,
        "template": template,
        "tpl_line1": tpl_line1,
        "tpl_line2": tpl_line2,
    }