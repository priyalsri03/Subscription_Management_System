from flask import Flask, render_template, session, redirect, url_for
from database import init_db
from modules.auth import auth
from modules.products import products
from modules.plans import plans
from modules.discounts import discounts
from modules.dashboard import get_dashboard_data

app = Flask(__name__)

app.config["SECRET_KEY"] = "replace-with-a-random-secret"

app.register_blueprint(auth)

app.register_blueprint(products)

app.register_blueprint(plans)

app.register_blueprint(discounts)

@app.route("/")
def home():
    return redirect(url_for("auth.login"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    data = get_dashboard_data()

    return render_template(
        "dashboard.html",
        name=session.get("name"),
        role=session.get("role"),
        data=data
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=True)