from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from bson.objectid import ObjectId

import os


# ==========================================================
# Load Environment Variables
# ==========================================================

load_dotenv()


# ==========================================================
# Flask App
# ==========================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "default-secret-key"
)


# ==========================================================
# MongoDB Connection
# ==========================================================

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError(
        "MONGO_URI is missing in .env file"
    )


client = MongoClient(MONGO_URI)

db = client["milk_management"]

milk_collection = db["milk_records"]


# ==========================================================
# Test MongoDB Connection
# ==========================================================

try:

    client.admin.command("ping")

    print("MongoDB connected successfully!")

except Exception as e:

    print("MongoDB connection failed:")
    print(e)


# ==========================================================
# Admin Credentials
# ==========================================================

ADMIN_USERNAME = os.getenv(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    "admin123"
)


# ==========================================================
# Admin Authentication Helper
# ==========================================================

def is_admin():

    return session.get(
        "admin_logged_in",
        False
    )


# ==========================================================
# HOME / MILK ENTRY
# ==========================================================

@app.route("/")
def index():

    current_date = datetime.now().strftime(
        "%Y-%m-%d"
    )

    return render_template(
        "index.html",
        current_date=current_date,
        is_admin=is_admin()
    )


# ==========================================================
# ADD MILK DATA
# ==========================================================

@app.route("/add", methods=["POST"])
def add_milk():

    try:

        # ----------------------------------------------
        # Get form data
        # ----------------------------------------------

        date = request.form.get("date")

        farmer_name = request.form.get(
            "farmer_name"
        )

        quantity = float(
            request.form.get("quantity")
        )

        quality = request.form.get(
            "quality"
        )

        fat_value = request.form.get("fat")

        snf_value = request.form.get("snf")

        price = float(
            request.form.get("price")
        )


        # ----------------------------------------------
        # Optional FAT / SNF
        # ----------------------------------------------

        fat = (
            float(fat_value)
            if fat_value
            else 0
        )

        snf = (
            float(snf_value)
            if snf_value
            else 0
        )


        # ----------------------------------------------
        # Validation
        # ----------------------------------------------

        if not farmer_name:

            flash(
                "Farmer name is required!",
                "error"
            )

            return redirect(
                url_for("index")
            )


        if quantity <= 0:

            flash(
                "Quantity must be greater than 0!",
                "error"
            )

            return redirect(
                url_for("index")
            )


        if price < 0:

            flash(
                "Price cannot be negative!",
                "error"
            )

            return redirect(
                url_for("index")
            )


        # ----------------------------------------------
        # Calculate Total
        # ----------------------------------------------

        total_amount = quantity * price


        # ----------------------------------------------
        # MongoDB Document
        # ----------------------------------------------

        milk_data = {

            "date": date,

            "farmer_name": farmer_name,

            "quantity": quantity,

            "quality": quality,

            "fat": fat,

            "snf": snf,

            "price_per_litre": price,

            "total_amount": total_amount,

            "created_at": datetime.now()

        }


        # ----------------------------------------------
        # Save to MongoDB
        # ----------------------------------------------

        milk_collection.insert_one(
            milk_data
        )


        flash(
            "Milk information saved successfully!",
            "success"
        )


        return redirect(
            url_for("index")
        )


    except ValueError:

        flash(
            "Please enter valid numeric values!",
            "error"
        )

        return redirect(
            url_for("index")
        )


    except Exception as e:

        print(
            "Error while saving milk data:",
            e
        )

        flash(
            "Something went wrong while saving data!",
            "error"
        )

        return redirect(
            url_for("index")
        )


# ==========================================================
# ADMIN LOGIN
# ==========================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    # ----------------------------------------------
    # Already logged in
    # ----------------------------------------------

    if is_admin():

        return redirect(
            url_for("dashboard")
        )


    # ----------------------------------------------
    # Login POST
    # ----------------------------------------------

    if request.method == "POST":

        username = request.form.get(
            "username"
        )

        password = request.form.get(
            "password"
        )


        # ------------------------------------------
        # Check credentials
        # ------------------------------------------

        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session["admin_logged_in"] = True

            session["admin_username"] = username


            flash(
                "Admin login successful!",
                "success"
            )


            return redirect(
                url_for("dashboard")
            )


        else:

            flash(
                "Invalid username or password!",
                "error"
            )


    return render_template(
        "admin_login.html"
    )


# ==========================================================
# ADMIN LOGOUT
# ==========================================================

@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin_logged_in",
        None
    )

    session.pop(
        "admin_username",
        None
    )


    flash(
        "Admin logged out successfully!",
        "success"
    )


    return redirect(
        url_for("index")
    )


# ==========================================================
# ADMIN DASHBOARD
# ==========================================================

@app.route("/dashboard")
def dashboard():

    # ----------------------------------------------
    # Admin protection
    # ----------------------------------------------

    if not is_admin():

        flash(
            "Please login as admin first!",
            "error"
        )

        return redirect(
            url_for("admin_login")
        )


    # ----------------------------------------------
    # Get records
    # ----------------------------------------------

    records = list(
        milk_collection.find().sort(
            "created_at",
            -1
        )
    )


    # ----------------------------------------------
    # Statistics
    # ----------------------------------------------

    total_records = len(records)


    total_quantity = sum(
        record.get(
            "quantity",
            0
        )
        for record in records
    )


    total_amount = sum(
        record.get(
            "total_amount",
            0
        )
        for record in records
    )


    average_price = 0


    if total_quantity > 0:

        average_price = (
            total_amount /
            total_quantity
        )


    # ----------------------------------------------
    # Today's records
    # ----------------------------------------------

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )


    today_records = [

        record

        for record in records

        if record.get("date") == today

    ]


    today_quantity = sum(
        record.get(
            "quantity",
            0
        )
        for record in today_records
    )


    today_amount = sum(
        record.get(
            "total_amount",
            0
        )
        for record in today_records
    )


    return render_template(

        "dashboard.html",

        records=records,

        total_records=total_records,

        total_quantity=total_quantity,

        total_amount=total_amount,

        average_price=round(
            average_price,
            2
        ),

        today_records=len(
            today_records
        ),

        today_quantity=today_quantity,

        today_amount=today_amount

    )


# ==========================================================
# ADMIN HISTORY
# ==========================================================

@app.route("/history")
def history():

    # ----------------------------------------------
    # Admin protection
    # ----------------------------------------------

    if not is_admin():

        flash(
            "Admin login required!",
            "error"
        )

        return redirect(
            url_for("admin_login")
        )


    records = list(

        milk_collection.find().sort(
            "created_at",
            -1
        )

    )


    return render_template(

        "history.html",

        records=records

    )


# ==========================================================
# DELETE MILK RECORD
# ==========================================================

@app.route(
    "/delete/<record_id>",
    methods=["POST"]
)
def delete_record(record_id):

    # ----------------------------------------------
    # Admin protection
    # ----------------------------------------------

    if not is_admin():

        flash(
            "Unauthorized access!",
            "error"
        )

        return redirect(
            url_for("admin_login")
        )


    try:

        milk_collection.delete_one({

            "_id": ObjectId(
                record_id
            )

        })


        flash(
            "Record deleted successfully!",
            "success"
        )


    except Exception as e:

        print(
            "Delete error:",
            e
        )


        flash(
            "Unable to delete record!",
            "error"
        )


    return redirect(
        url_for("history")
    )


# ==========================================================
# 404 ERROR
# ==========================================================

@app.errorhandler(404)
def page_not_found(error):

    return """

    <h1>404 - Page Not Found</h1>

    <a href="/">Go Home</a>

    """, 404


# ==========================================================
# RUN APP
# ==========================================================

if __name__ == "__main__":

    app.run(

        debug=True,

        host="0.0.0.0",

        port=5000

    )