
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db

products = Blueprint("products", __name__)


def admin_required():
    return "user_id" in session and session.get("role") == "admin"


@products.route("/products")
def product_list():
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db()
    all_products = conn.execute(
        "SELECT * FROM products ORDER BY id DESC"
    ).fetchall()

    variants = conn.execute(
        "SELECT * FROM product_variants ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return render_template(
        "products.html",
        products=all_products,
        variants=variants
    )


@products.route("/products/add", methods=["POST"])
def add_product():
    if not admin_required():
        return redirect(url_for("auth.login"))

    name = request.form.get("name", "").strip()
    product_type = request.form.get("product_type", "").strip()
    sales_price = request.form.get("sales_price", "0")
    cost_price = request.form.get("cost_price", "0")
    notes = request.form.get("notes", "").strip()

    if not name:
        flash("Product name is required.")
        return redirect(url_for("products.product_list"))

    try:
        sales_price = float(sales_price)
        cost_price = float(cost_price)

        if sales_price < 0 or cost_price < 0:
            raise ValueError

        conn = get_db()
        conn.execute("""
            INSERT INTO products
            (name, product_type, sales_price, cost_price, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (name, product_type, sales_price, cost_price, notes))

        conn.commit()
        conn.close()

        flash("Product added successfully!")

    except ValueError:
        flash("Please enter valid, non-negative prices.")

    return redirect(url_for("products.product_list"))


@products.route("/products/edit/<int:product_id>", methods=["POST"])
def edit_product(product_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    name = request.form.get("name", "").strip()
    product_type = request.form.get("product_type", "").strip()
    notes = request.form.get("notes", "").strip()

    try:
        sales_price = float(request.form.get("sales_price", "0"))
        cost_price = float(request.form.get("cost_price", "0"))

        if not name or sales_price < 0 or cost_price < 0:
            raise ValueError

        conn = get_db()
        conn.execute("""
            UPDATE products
            SET name=?, product_type=?, sales_price=?, cost_price=?, notes=?
            WHERE id=?
        """, (name, product_type, sales_price, cost_price, notes, product_id))

        conn.commit()
        conn.close()
        flash("Product updated successfully!")

    except ValueError:
        flash("Please enter valid product details.")

    return redirect(url_for("products.product_list"))


@products.route("/products/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db()

    conn.execute(
        "DELETE FROM product_variants WHERE product_id=?",
        (product_id,)
    )
    conn.execute(
        "DELETE FROM products WHERE id=?",
        (product_id,)
    )

    conn.commit()
    conn.close()

    flash("Product deleted successfully!")
    return redirect(url_for("products.product_list"))


@products.route("/products/<int:product_id>/variant", methods=["POST"])
def add_variant(product_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    variant_name = request.form.get("variant_name", "").strip()

    if not variant_name:
        flash("Variant name is required.")
        return redirect(url_for("products.product_list"))

    # Odoo brand variant has an additional charge of Rs. 560
    extra_price = 560 if variant_name.lower() == "odoo" else 0

    conn = get_db()

    product = conn.execute(
        "SELECT id FROM products WHERE id=?",
        (product_id,)
    ).fetchone()

    if product:
        conn.execute("""
            INSERT INTO product_variants
            (product_id, variant_name, extra_price)
            VALUES (?, ?, ?)
        """, (product_id, variant_name, extra_price))

        conn.commit()
        flash("Variant added successfully!")
    else:
        flash("Product not found.")

    conn.close()
    return redirect(url_for("products.product_list"))
