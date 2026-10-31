
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db

discounts = Blueprint("discounts", __name__)


def admin_required():
    return "user_id" in session and session.get("role") == "admin"


@discounts.route("/discounts")
def discount_list():
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db()
    all_discounts = conn.execute(
        "SELECT * FROM discounts ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("discounts.html", discounts=all_discounts)


@discounts.route("/discounts/add", methods=["POST"])
def add_discount():
    if not admin_required():
        return redirect(url_for("auth.login"))

    name = request.form.get("name", "").strip()
    discount_type = request.form.get("discount_type", "")
    applies_to = request.form.get("applies_to", "")

    try:
        discount_value = float(request.form.get("discount_value", "0"))
        min_purchase = float(request.form.get("min_purchase", "0"))
        min_quantity = int(request.form.get("min_quantity", "1"))
        usage_limit = int(request.form.get("usage_limit", "1"))

        start_date = request.form.get("start_date") or None
        end_date = request.form.get("end_date") or None

        if not name:
            raise ValueError

        if discount_type not in ["fixed", "percentage"]:
            raise ValueError

        if applies_to not in ["products", "subscriptions", "both"]:
            raise ValueError

        if discount_value < 0 or min_purchase < 0:
            raise ValueError

        if discount_type == "percentage" and discount_value > 100:
            raise ValueError

        if min_quantity < 1 or usage_limit < 1:
            raise ValueError

        if start_date and end_date and end_date < start_date:
            raise ValueError

        conn = get_db()
        conn.execute("""
            INSERT INTO discounts
            (name, discount_type, discount_value, start_date, end_date,
             usage_limit, min_purchase, min_quantity, applies_to, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            name, discount_type, discount_value, start_date, end_date,
            usage_limit, min_purchase, min_quantity, applies_to
        ))

        conn.commit()
        conn.close()

        flash("Discount created successfully!")

    except ValueError:
        flash("Please enter valid discount details.")

    return redirect(url_for("discounts.discount_list"))




@discounts.route("/discounts/edit/<int:discount_id>", methods=["POST"])
def edit_discount(discount_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    name = request.form.get("name", "").strip()
    discount_type = request.form.get("discount_type", "")
    applies_to = request.form.get("applies_to", "")

    try:
        value = float(request.form.get("discount_value", "0"))
        min_purchase = float(request.form.get("min_purchase", "0"))
        min_quantity = int(request.form.get("min_quantity", "1"))
        usage_limit = int(request.form.get("usage_limit", "1"))

        start_date = request.form.get("start_date") or None
        end_date = request.form.get("end_date") or None

        if not name or discount_type not in ["fixed", "percentage"]:
            raise ValueError

        if applies_to not in ["products", "subscriptions", "both"]:
            raise ValueError

        if value < 0 or min_purchase < 0:
            raise ValueError

        if discount_type == "percentage" and value > 100:
            raise ValueError

        if min_quantity < 1 or usage_limit < 1:
            raise ValueError

        if start_date and end_date and end_date < start_date:
            raise ValueError

        conn = get_db()
        conn.execute("""
            UPDATE discounts
            SET name=?, discount_type=?, discount_value=?,
                start_date=?, end_date=?, usage_limit=?,
                min_purchase=?, min_quantity=?, applies_to=?
            WHERE id=?
        """, (
            name, discount_type, value, start_date, end_date,
            usage_limit, min_purchase, min_quantity, applies_to,
            discount_id
        ))

        conn.commit()
        conn.close()
        flash("Discount updated successfully!")

    except ValueError:
        flash("Please enter valid discount details.")

    return redirect(url_for("discounts.discount_list"))


@discounts.route("/discounts/delete/<int:discount_id>", methods=["POST"])
def delete_discount(discount_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db()
    conn.execute("DELETE FROM discounts WHERE id=?", (discount_id,))
    conn.commit()
    conn.close()

    flash("Discount deleted successfully!")
    return redirect(url_for("discounts.discount_list"))
