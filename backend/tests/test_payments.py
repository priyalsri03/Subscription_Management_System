"""
Tests for Payment Management - Person 2
"""
import pytest
from datetime import date, timedelta


def test_record_payment(client, db, sample_data, mock_auth):
    """Test recording a payment against an invoice."""
    # Create subscription and invoice
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
            "lines": [
                {"product_id": sample_data["product1"].id, "quantity": 1}
            ],
        },
    )
    sub_id = response.json()["id"]
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})

    response = client.post(
        "/api/v1/invoices",
        json={
            "subscription_id": sub_id,
            "period_start": str(date.today()),
            "period_end": str(date.today()),
        },
    )
    inv_id = response.json()["id"]
    inv_total = response.json()["total"]

    # Record payment
    response = client.post(
        "/api/v1/payments",
        json={
            "invoice_id": inv_id,
            "amount": inv_total,
            "method": "bank_transfer",
            "note": "Test payment",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["invoice_id"] == inv_id
    assert data["method"] == "bank_transfer"


def test_multiple_payments_partial(client, db, sample_data, mock_auth):
    """Test recording multiple partial payments against an invoice."""
    # Create invoice
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
            "lines": [
                {"product_id": sample_data["product1"].id, "quantity": 1}
            ],
        },
    )
    sub_id = response.json()["id"]
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})

    response = client.post(
        "/api/v1/invoices",
        json={
            "subscription_id": sub_id,
            "period_start": str(date.today()),
            "period_end": str(date.today()),
        },
    )
    inv_id = response.json()["id"]
    inv_total = float(response.json()["total"])

    # Partial payment 1
    partial1 = client.post(
        "/api/v1/payments",
        json={
            "invoice_id": inv_id,
            "amount": inv_total * 0.5,
            "method": "cash",
        },
    )
    assert partial1.status_code == 201

    # Partial payment 2
    partial2 = client.post(
        "/api/v1/payments",
        json={
            "invoice_id": inv_id,
            "amount": inv_total * 0.5,
            "method": "cash",
        },
    )
    assert partial2.status_code == 201

    # Check invoice is marked paid
    response = client.get(f"/api/v1/invoices/{inv_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "paid"


def test_list_payments(client, db, sample_data, mock_auth):
    """Test listing payments."""
    response = client.get("/api/v1/payments")
    assert response.status_code == 200


def test_get_payment_by_id(client, db, sample_data, mock_auth):
    """Test getting payment by ID."""
    # Create invoice and payment
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
            "lines": [
                {"product_id": sample_data["product1"].id, "quantity": 1}
            ],
        },
    )
    sub_id = response.json()["id"]
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})

    response = client.post(
        "/api/v1/invoices",
        json={
            "subscription_id": sub_id,
            "period_start": str(date.today()),
            "period_end": str(date.today()),
        },
    )
    inv_id = response.json()["id"]
    inv_total = float(response.json()["total"])

    response = client.post(
        "/api/v1/payments",
        json={
            "invoice_id": inv_id,
            "amount": inv_total,
            "method": "cash",
        },
    )
    pay_id = response.json()["id"]

    response = client.get(f"/api/v1/payments/{pay_id}")
    assert response.status_code == 200
    assert response.json()["id"] == pay_id


def test_get_outstanding_amount(client, db, sample_data, mock_auth):
    """Test getting outstanding amount for an invoice."""
    # Create invoice with full payment
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
            "lines": [
                {"product_id": sample_data["product1"].id, "quantity": 1}
            ],
        },
    )
    sub_id = response.json()["id"]
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})

    response = client.post(
        "/api/v1/invoices",
        json={
            "subscription_id": sub_id,
            "period_start": str(date.today()),
            "period_end": str(date.today()),
        },
    )
    inv_id = response.json()["id"]
    inv_total = float(response.json()["total"])

    # Full payment
    client.post(
        "/api/v1/payments",
        json={
            "invoice_id": inv_id,
            "amount": inv_total,
            "method": "cash",
        },
    )

    # Get outstanding
    response = client.get(f"/api/v1/payments/invoice/{inv_id}/outstanding")
    assert response.status_code == 200
    assert float(response.json()["outstanding"]) == 0


def test_cannot_pay_cancelled_invoice(client, db, sample_data, mock_auth):
    """Test that payments cannot be recorded on cancelled invoices."""
    # Create and cancel invoice
    response = client.post(
        "/api/v1/subscriptions",
        json={
            "customer_id": sample_data["customer"].id,
            "plan_id": sample_data["plan1"].id,
            "start_date": str(date.today()),
            "lines": [
                {"product_id": sample_data["product1"].id, "quantity": 1}
            ],
        },
    )
    sub_id = response.json()["id"]
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "confirmed"})
    client.post(f"/api/v1/subscriptions/{sub_id}/status", json={"new_status": "active"})

    response = client.post(
        "/api/v1/invoices",
        json={
            "subscription_id": sub_id,
            "period_start": str(date.today()),
            "period_end": str(date.today()),
        },
    )
    inv_id = response.json()["id"]

    # Cancel invoice
    client.post(f"/api/v1/invoices/{inv_id}/cancel")

    # Try to pay cancelled invoice
    response = client.post(
        "/api/v1/payments",
        json={
            "invoice_id": inv_id,
            "amount": 100,
            "method": "cash",
        },
    )
    assert response.status_code == 400