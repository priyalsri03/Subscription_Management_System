"""
End-to-end Subscription Flow Tests - Person 2
Tests the complete flow from template to payment.
"""
import pytest
from datetime import date, timedelta


def test_complete_subscription_flow(client, db, sample_data, mock_auth):
    """Test complete subscription -> invoice -> payment flow."""
    customer = sample_data["customer"]
    template = sample_data["template"]

    # Step 1: Create subscription from template
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "template_id": template.id,
            "customer_id": customer.id,
            "start_date": str(date.today()),
            "payment_terms": "net_30",
        },
    )
    assert response.status_code == 201
    sub_data = response.json()
    sub_id = sub_data["id"]
    assert sub_data["status"] == "draft"
    assert sub_data["number"].startswith("SUB-")

    # Step 2: Move to confirmed
    response = client.post(
        f"/api/v1/subscriptions/{sub_id}/status",
        json={"new_status": "confirmed"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"

    # Step 3: Activate subscription
    response = client.post(
        f"/api/v1/subscriptions/{sub_id}/status",
        json={"new_status": "active"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "active"

    # Step 4: Generate invoice
    today = date.today()
    response = client.post(
        "/api/v1/invoices",
        json={
            "subscription_id": sub_id,
            "period_start": str(today),
            "period_end": str(today + timedelta(days=30)),
        },
    )
    assert response.status_code == 201
    inv_data = response.json()
    inv_id = inv_data["id"]
    assert inv_data["status"] == "draft"

    # Step 5: Confirm invoice
    response = client.post(f"/api/v1/invoices/{inv_id}/confirm")
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"

    # Step 6: Record payment
    response = client.post(
        "/api/v1/payments",
        json={
            "invoice_id": inv_id,
            "amount": float(inv_data["total"]),
            "method": "bank_transfer",
            "note": "Full payment via bank",
        },
    )
    assert response.status_code == 201

    # Step 7: Verify invoice is now paid
    response = client.get(f"/api/v1/invoices/{inv_id}")
    assert response.json()["status"] == "paid"
    assert float(response.json()["amount_paid"]) >= float(response.json()["total"])


def test_subscription_with_variant(client, db, sample_data, mock_auth):
    """Test subscription with product variant (Odoo brand with ₹560 extra)."""
    customer = sample_data["customer"]
    product = sample_data["product1"]
    variant = sample_data["variant1"]  # Odoo with 560 extra

    # Create subscription with variant
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": customer.id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
            "lines": [
                {"product_id": product.id, "variant_id": variant.id, "quantity": 1}
            ],
        },
    )
    assert response.status_code == 201
    sub_data = response.json()

    # Calculate expected price: 1000 + 560 = 1560
    expected_price = float(product.sales_price) + float(variant.extra_price)
    assert float(sub_data["lines"][0]["unit_price"]) == expected_price


def test_subscription_with_tax(client, db, sample_data, mock_auth):
    """Test subscription with tax calculation."""
    customer = sample_data["customer"]
    tax = sample_data["tax1"]  # 18% GST

    # Create subscription
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": customer.id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
            "lines": [
                {"product_id": sample_data["product1"].id, "quantity": 1, "tax_id": tax.id}
            ],
        },
    )
    assert response.status_code == 201


def test_billing_cycle_bulk(client, db, sample_data, mock_auth):
    """Test bulk invoice generation via billing cycle."""
    # Create multiple active subscriptions
    customers = []
    for i in range(3):
        cust = client.post(
            "/api/v1/auth/register",
            json={
                "name": f"Customer {i}",
                "email": f"customer{i}@test.com",
                "password": "TestPass123!@#",
                "role": "customer",
            },
        )
        if cust.status_code == 201:
            customers.append(cust.json()["id"])
        else:
            # Customer might exist, skip
            pass

    # Create subscriptions
    for cust_id in [sample_data["customer"].id, 12345]:  # Use existing and potential new
        response = client.post(
            "/api/v1/subscriptions",
            json={
                "customer_id": cust_id,
                "plan_id": sample_data["plan1"].id,
                "start_date": str(date.today() - timedelta(days=1)),
            },
        )
        if response.status_code == 201:
            sub_id = response.json()["id"]
            client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
            client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})

    # Run billing cycle
    response = client.post("/api/v1/invoices/billing-cycle")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1  # At least one invoice created

    # Verify no duplicates (unique constraint)
    # This would fail if double-billing prevention doesn't work
    response = client.post("/api/v1/invoices/billing-cycle")
    assert response.status_code == 200
    assert len(response.json()) == 0  # No new invoices (already billed)