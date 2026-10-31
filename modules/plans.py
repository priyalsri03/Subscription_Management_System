
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db

plans = Blueprint("plans", __name__)


def admin_required():
    return "user_id" in session and session.get("role") == "admin"


@plans.route("/plans")
def plan_list():
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db()
    all_plans = conn.execute(
        "SELECT * FROM plans ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("plans.html", plans=all_plans)


@plans.route("/plans/add", methods=["POST"])
def add_plan():
    if not admin_required():
        return redirect(url_for("auth.login"))

    name = request.form.get("name", "").strip()
    billing_cycle = request.form.get("billing_cycle", "")
    minimum_quantity = request.form.get("minimum_quantity", "1")
    start_date = request.form.get("start_date") or None
    end_date = request.form.get("end_date") or None

    allowed_cycles = ["Daily", "Weekly", "Monthly", "Yearly"]

    try:
        minimum_quantity = int(minimum_quantity)

        if not name or billing_cycle not in allowed_cycles:
            raise ValueError

        if minimum_quantity < 1:
            raise ValueError

        if start_date and end_date and end_date < start_date:
            raise ValueError

        conn = get_db()
        conn.execute("""
            INSERT INTO plans
            (name, billing_cycle, minimum_quantity, start_date, end_date)
            VALUES (?, ?, ?, ?, ?)
        """, (name, billing_cycle, minimum_quantity, start_date, end_date))

        conn.commit()
        conn.close()

        flash("Plan created successfully!")

    except ValueError:
        flash("Please enter valid plan details.")

    return redirect(url_for("plans.plan_list"))


@plans.route("/plans/edit/<int:plan_id>", methods=["POST"])
def edit_plan(plan_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    name = request.form.get("name", "").strip()
    billing_cycle = request.form.get("billing_cycle", "")
    start_date = request.form.get("start_date") or None
    end_date = request.form.get("end_date") or None

    try:
        minimum_quantity = int(request.form.get("minimum_quantity", "1"))

        if not name or billing_cycle not in ["Daily", "Weekly", "Monthly", "Yearly"]:
            raise ValueError

        if minimum_quantity < 1:
            raise ValueError

        if start_date and end_date and end_date < start_date:
            raise ValueError

        conn = get_db()
        conn.execute("""
            UPDATE plans
            SET name=?, billing_cycle=?, minimum_quantity=?,
                start_date=?, end_date=?
            WHERE id=?
        """, (name, billing_cycle, minimum_quantity,
              start_date, end_date, plan_id))

        conn.commit()
        conn.close()

        flash("Plan updated successfully!")

    except ValueError:
        flash("Please enter valid plan details.")

    return redirect(url_for("plans.plan_list"))


@plans.route("/plans/delete/<int:plan_id>", methods=["POST"])
def delete_plan(plan_id):
    if not admin_required():
        return redirect(url_for("auth.login"))

    conn = get_db()

    try:
        conn.execute("DELETE FROM plans WHERE id=?", (plan_id,))
        conn.commit()
        flash("Plan deleted successfully!")
    except Exception:
        conn.rollback()
        flash("This plan may already be linked to a subscription.")

    conn.close()
    return redirect(url_for("plans.plan_list"))
