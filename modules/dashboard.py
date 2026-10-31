
from database import get_db


def get_dashboard_data():
    conn = get_db()

    total_products = conn.execute(
        "SELECT COUNT(*) FROM products"
    ).fetchone()[0]

    total_plans = conn.execute(
        "SELECT COUNT(*) FROM plans"
    ).fetchone()[0]

    active_subscriptions = conn.execute(
        "SELECT COUNT(*) FROM subscriptions WHERE status = 'Active'"
    ).fetchone()[0]

    revenue_received = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) FROM payments"
    ).fetchone()[0]

    outstanding_amount = conn.execute("""
        SELECT COALESCE(SUM(
            invoices.total_amount -
            COALESCE((
                SELECT SUM(payments.amount)
                FROM payments
                WHERE payments.invoice_id = invoices.id
            ), 0)
        ), 0)
        FROM invoices
    """).fetchone()[0]

    total_invoices = conn.execute(
        "SELECT COUNT(*) FROM invoices"
    ).fetchone()[0]

    conn.close()

    return {
        "total_products": total_products,
        "total_plans": total_plans,
        "active_subscriptions": active_subscriptions,
        "revenue_received": round(revenue_received, 2),
        "outstanding_amount": round(max(outstanding_amount, 0), 2),
        "total_invoices": total_invoices
    }
