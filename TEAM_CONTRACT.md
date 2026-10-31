# Team Contract - Subscription Management System

Agreed by Person 1 and Person 2 before coding, so both halves plug together.
To change something, edit this file in a pull request.

## 1. Stack

- Python 3.11+, FastAPI, SQLAlchemy 2.x (ORM), Pydantic, pytest
- Database: SQLite locally. The hosted version uses PostgreSQL through the `DATABASE_URL` setting, with no code change.
- Login: JWT tokens. Passwords are hashed with bcrypt.
- Money: `Decimal`, stored as `Numeric(12,2)`. Currency is INR (₹).
- API prefix: `/api/v1/...`. Errors are JSON: `{"detail": "..."}`.

## 2. Who owns which files

Only edit your own files. Shared files (marked "shared") change only through small pull requests.

```
backend/app/
  main.py                      shared (Person 1 creates it; each person adds their own router line)
  core/config.py db.py security.py      Person 1
  models/user.py product.py plan.py discount.py tax.py                Person 1
  models/quotation.py subscription.py invoice.py payment.py           Person 2
  api/auth.py products.py plans.py discounts.py taxes.py dashboard.py Person 1
  api/quotations.py subscriptions.py invoices.py payments.py          Person 2
  services/pricing.py discounts.py taxes.py                           Person 1
  services/subscriptions.py billing.py payments.py                    Person 2
backend/tests/
  test_auth*.py test_products*.py test_plans*.py test_discounts*.py   Person 1
  test_subscription_flow.py test_payments.py                          Person 2
```

## 3. Tables and key fields

### Person 1 owns

- `users`: id, name, email (unique), password_hash, role, is_active, created_at
- `products`: id, name, type, sales_price, cost_price, notes
- `product_variants`: id, product_id, attribute (e.g. brand), value (e.g. Odoo), extra_price (e.g. 560)
- `plans`: id, name, price, billing_period, min_quantity, available_from, available_to, auto_close, allow_early_close, allow_pause, allow_renew
- `discounts`: id, name, kind (fixed or percent), value, min_purchase, min_quantity, start_date, end_date, usage_limit, times_used, applies_to (product or subscription), product_id (optional)
- `taxes`: id, name, rate_percent (owner still to confirm, see section 7)

### Person 2 owns

- `quotation_templates`: id, name, plan_id, validity_days
- `quotation_template_lines`: id, template_id, product_id, variant_id, quantity
- `subscriptions`: id, number (unique), customer_id (users.id), plan_id, start_date, expiry_date, payment_terms, status, is_paused
- `subscription_lines`: id, subscription_id, product_id, variant_id, quantity, unit_price, tax_id, amount
- `invoices`: id, number (unique), subscription_id, customer_id, period_start, period_end, issue_date, due_date, status, subtotal, discount_total, tax_total, total, amount_paid. **Unique on (subscription_id, period_start)** so nothing is billed twice.
- `invoice_lines`: id, invoice_id, product_id, description, quantity, unit_price, tax_amount, amount
- `payments`: id, invoice_id, method, amount, paid_on, note

## 4. Hand-off functions

```python
# Person 1 provides
core/security.py:      get_current_user() -> User
                       require_role(*roles)                 # FastAPI dependency
services/pricing.py:   unit_price(product_id, variant_id=None) -> Decimal   # sales price + variant extra
services/taxes.py:     calculate_tax(amount: Decimal, tax_id: int) -> Decimal
services/discounts.py: find_discounts(customer_id, lines, subtotal, on_date) -> list[AppliedDiscount]
                       mark_discount_used(discount_id) -> None   # Person 2 calls this when an invoice is confirmed
# AppliedDiscount = discount_id, name, amount (Decimal)

# Person 2 provides (for the dashboard)
services/billing.py:   active_subscription_count() -> int
                       revenue_summary(date_from, date_to) -> {invoiced, paid, outstanding}
                       overdue_invoices() -> list[Invoice]
```

Until a function exists, the other person uses a clearly marked temporary stand-in (`# TEMP`) and removes it once the real one is merged.

## 5. Fixed values (lowercase strings)

- Roles: `admin`, `staff`, `customer`
- Subscription status: `draft`, `quotation`, `confirmed`, `active`, `closed`. Pause is a separate true/false flag (`is_paused`), not a status.
- Invoice status: `draft`, `confirmed`, `paid`, `cancelled`
- Billing period: `daily`, `weekly`, `monthly`, `yearly`
- Overdue is worked out, not stored: invoice is `confirmed`, due_date is before today, and amount_paid is less than total.

## 6. Git rules

- Branch names: `p1/<short-task>` and `p2/<short-task>`, merged into `main` with a pull request.
- Pull `main` before you start work each day.
- Never commit `.env`, `*.db` files, passwords or keys. Only `.env.example` goes in Git.
- Never force-push `main`. Tests should pass before merging.

## 7. Still to decide

- Tax rules (admin sets them, invoices use them): proposal is Person 1, as part of billing rules.
- Password-reset email link: proposal is Person 1, as part of authentication.
- Customer portal screens (customer sees only their own subscriptions and invoices): proposal is Person 2 for the subscription and invoice screens, using Person 1's role check.
- Screens: one UI tool (v0 or Lovable) or plain HTML/JS served by the backend, and the visual style.
