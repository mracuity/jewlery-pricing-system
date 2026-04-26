from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from models.db_setup import generate_product_code, get_connection, init_db
from utils.excel_export import export_products_to_excel
from utils.pricing_engine import calculate_price, load_config, save_config


BASE_DIR = Path(__file__).resolve().parent
CATEGORIES = ["Ring", "Necklace", "Bracelet"]
METAL_TYPES = ["Gold 14k", "Gold 18k", "Platinum"]

app = Flask(__name__)
app.secret_key = "local-jewelry-pricing-tool"


@app.context_processor
def inject_globals():
    return {
        "config": load_config(),
        "categories": CATEGORIES,
        "metal_types": METAL_TYPES,
    }


def parse_product_form(form):
    category = form.get("category", "").strip()
    metal_type = form.get("metal_type", "").strip()
    if category not in CATEGORIES:
        raise ValueError("Choose a valid category.")
    if metal_type not in METAL_TYPES:
        raise ValueError("Choose a valid metal type.")

    try:
        data = {
            "client_name": form.get("client_name", "").strip(),
            "category": category,
            "metal_type": metal_type,
            "metal_weight": float(form.get("metal_weight", 0)),
            "diamond_weight": float(form.get("diamond_weight", 0)),
            "diamond_pcs": int(form.get("diamond_pcs", 0)),
            "diamond_rate": float(form.get("diamond_rate", 0)),
            "labor_rate": float(form.get("labor_rate", 0)),
            "setting_charge_per_pc": float(form.get("setting_charge_per_pc", 0)),
            "gold_loss": float(form.get("gold_loss", 0)),
            "rhodium": float(form.get("rhodium", 0)),
            "extra_charges": float(form.get("extra_charges", 0)),
            "margin": float(form.get("margin", 0)),
        }
    except ValueError as exc:
        raise ValueError("Enter valid numbers for pricing fields.") from exc

    calculate_product_price(data)
    return data


def calculate_product_price(data):
    return calculate_price(
        data["metal_type"],
        data["metal_weight"],
        data["diamond_weight"],
        data["diamond_rate"],
        data["diamond_pcs"],
        data["labor_rate"],
        data["setting_charge_per_pc"],
        data["gold_loss"],
        data["rhodium"],
        data["extra_charges"],
        data["margin"],
    )


def fetch_product(product_id):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()


def fetch_products(search="", category="", sort="newest"):
    query = "SELECT * FROM products WHERE 1 = 1"
    params = []

    if search:
        query += " AND (product_code LIKE ? OR client_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    if category in CATEGORIES:
        query += " AND category = ?"
        params.append(category)

    sort_map = {
        "price_asc": "final_price ASC",
        "price_desc": "final_price DESC",
        "oldest": "datetime(created_at) ASC",
        "newest": "datetime(created_at) DESC",
    }
    query += f" ORDER BY {sort_map.get(sort, sort_map['newest'])}"

    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def product_insert_values(product_code, data, final_price):
    return (
        product_code,
        data["client_name"],
        data["category"],
        data["metal_type"],
        data["metal_weight"],
        data["diamond_weight"],
        data["diamond_pcs"],
        data["diamond_rate"],
        0,
        data["labor_rate"],
        data["setting_charge_per_pc"],
        data["gold_loss"],
        data["rhodium"],
        data["extra_charges"],
        data["margin"],
        final_price,
    )


@app.route("/")
def dashboard():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    sort = request.args.get("sort", "newest")
    products = fetch_products(search, category, sort)
    totals = {
        "count": len(products),
        "inventory_value": sum(float(product["final_price"]) for product in products),
    }
    return render_template(
        "dashboard.html",
        products=products,
        search=search,
        selected_category=category,
        sort=sort,
        totals=totals,
    )


@app.route("/add", methods=["GET", "POST"])
def add_product():
    defaults = load_config()
    if request.method == "POST":
        try:
            data = parse_product_form(request.form)
            breakdown = calculate_product_price(data)
            product_code = generate_product_code(data["category"])
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO products (
                        product_code, client_name, category, metal_type, metal_weight, diamond_weight,
                        diamond_pcs, diamond_rate, making_charges, labor_rate,
                        setting_charge_per_pc, gold_loss, rhodium, extra_charges,
                        margin, final_price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    product_insert_values(product_code, data, breakdown["final_price"]),
                )
                conn.commit()
            flash(f"Product {product_code} added.", "success")
            return redirect(url_for("dashboard"))
        except ValueError as exc:
            flash(str(exc), "error")

    form_data = {
        "client_name": request.form.get("client_name", ""),
        "category": request.form.get("category", "Ring"),
        "metal_type": request.form.get("metal_type", "Gold 18k"),
        "diamond_rate": request.form.get("diamond_rate", defaults.get("diamond_base_rate", 0)),
        "diamond_pcs": request.form.get("diamond_pcs", 0),
        "labor_rate": request.form.get("labor_rate", defaults.get("labor_rate", 0)),
        "setting_charge_per_pc": request.form.get(
            "setting_charge_per_pc", defaults.get("setting_charge_per_pc", 0)
        ),
        "gold_loss": request.form.get("gold_loss", defaults.get("default_gold_loss", 0)),
        "rhodium": request.form.get("rhodium", defaults.get("default_rhodium", 0)),
        "extra_charges": request.form.get("extra_charges", 0),
        "margin": request.form.get("margin", defaults.get("default_margin", 0)),
    }
    return render_template("add_product.html", product=form_data)


@app.route("/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    product = fetch_product(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        try:
            data = parse_product_form(request.form)
            breakdown = calculate_product_price(data)
            with get_connection() as conn:
                conn.execute(
                    """
                    UPDATE products
                    SET client_name = ?, category = ?, metal_type = ?, metal_weight = ?, diamond_weight = ?,
                        diamond_pcs = ?, diamond_rate = ?, making_charges = ?,
                        labor_rate = ?, setting_charge_per_pc = ?, gold_loss = ?,
                        rhodium = ?, extra_charges = ?, margin = ?, final_price = ?
                    WHERE id = ?
                    """,
                    (
                        data["client_name"],
                        data["category"],
                        data["metal_type"],
                        data["metal_weight"],
                        data["diamond_weight"],
                        data["diamond_pcs"],
                        data["diamond_rate"],
                        0,
                        data["labor_rate"],
                        data["setting_charge_per_pc"],
                        data["gold_loss"],
                        data["rhodium"],
                        data["extra_charges"],
                        data["margin"],
                        breakdown["final_price"],
                        product_id,
                    ),
                )
                conn.commit()
            flash("Product updated.", "success")
            return redirect(url_for("dashboard"))
        except ValueError as exc:
            flash(str(exc), "error")

    return render_template("edit_product.html", product=product)


@app.route("/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    product = fetch_product(product_id)
    if not product:
        flash("Product not found.", "error")
    else:
        with get_connection() as conn:
            conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()
        flash(f"Product {product['product_code']} deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/duplicate/<int:product_id>", methods=["POST"])
def duplicate_product(product_id):
    product = fetch_product(product_id)
    if not product:
        flash("Product not found.", "error")
        return redirect(url_for("dashboard"))

    data = dict(product)
    product_code = generate_product_code(product["category"])
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO products (
                product_code, client_name, category, metal_type, metal_weight, diamond_weight,
                diamond_pcs, diamond_rate, making_charges, labor_rate,
                setting_charge_per_pc, gold_loss, rhodium, extra_charges,
                margin, final_price
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            product_insert_values(product_code, data, product["final_price"]),
        )
        conn.commit()
    flash(f"Product duplicated as {product_code}.", "success")
    return redirect(url_for("dashboard"))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    current_config = load_config()
    if request.method == "POST":
        try:
            updated_config = {
                "gold_rate": float(request.form.get("gold_rate", 0)),
                "diamond_base_rate": float(request.form.get("diamond_base_rate", 0)),
                "default_margin": float(request.form.get("default_margin", 0)),
                "currency_symbol": request.form.get("currency_symbol", "").strip() or "$",
                "platinum_rate": float(request.form.get("platinum_rate", 0)),
                "labor_rate": float(request.form.get("labor_rate", 0)),
                "setting_charge_per_pc": float(request.form.get("setting_charge_per_pc", 0)),
                "default_gold_loss": float(request.form.get("default_gold_loss", 0)),
                "default_rhodium": float(request.form.get("default_rhodium", 0)),
            }
            if min(
                updated_config["gold_rate"],
                updated_config["diamond_base_rate"],
                updated_config["default_margin"],
                updated_config["platinum_rate"],
                updated_config["labor_rate"],
                updated_config["setting_charge_per_pc"],
                updated_config["default_gold_loss"],
                updated_config["default_rhodium"],
            ) < 0:
                raise ValueError
            save_config(updated_config)
            flash("Settings saved.", "success")
            return redirect(url_for("settings"))
        except ValueError:
            flash("Settings must contain valid non-negative numbers.", "error")
    return render_template("settings.html", settings=current_config)


@app.route("/export")
def export():
    products = fetch_products(sort="newest")
    if not products:
        flash("No products to export.", "error")
        return redirect(url_for("dashboard"))
    export_path = export_products_to_excel(products)
    return send_file(
        export_path,
        as_attachment=True,
        download_name="jewelry_products.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


import os

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))