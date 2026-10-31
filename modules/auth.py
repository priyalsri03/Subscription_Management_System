import re
from flask import Blueprint, request, redirect, url_for
from flask import render_template, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db

auth = Blueprint("auth", __name__)


def valid_password(password):
    return (
        len(password) > 8
        and re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"[^A-Za-z0-9]", password)
    )


@auth.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.")
            return redirect(url_for("auth.signup"))

        if not valid_password(password):
            flash("Password must be over 8 characters with uppercase, lowercase and special character.")
            return redirect(url_for("auth.signup"))

        conn = get_db()

        try:
            hashed_password = generate_password_hash(password)

            conn.execute(
                """INSERT INTO users (name, email, password, role)
                   VALUES (?, ?, ?, 'customer')""",
                (name, email, hashed_password)
            )

            conn.commit()
            flash("Account created successfully!")
            return redirect(url_for("auth.login"))

        except Exception:
            flash("Email may already be registered.")

        finally:
            conn.close()

    return render_template("signup.html")


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        conn.close()

        if user and check_password_hash(user["password"], password):

            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["name"] = user["name"]

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


@auth.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("auth.login"))