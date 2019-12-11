from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import werkzeug

from validators import RequestValidator, BalanceValidator
from helpers import apology, login_required, lookup, usd
from db_request import DBrequest

# Configure application
app = Flask(__name__)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    """Deposit money"""
    if request.method == "POST":
        if not RequestValidator(request.form).validate_deposit():
            row = DBrequest().select_cash(session["user_id"]).fetchone()
            cash = round(row[0], 2)
            deposit = round(float(request.form.get("amount")), 2)
            new_cash = round(cash + deposit, 2)

            DBrequest().update_user(new_cash, session["user_id"])
            data = {
                "cash": cash,
                "deposit": deposit,
                "current_cash": new_cash,
            }
            return render_template("current_balance.html", data=data)
    else:
        return render_template("deposit.html")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    rows = DBrequest().select_index(session["user_id"])
    stocks = []
    total = 0
    cash = DBrequest().select_cash(session["user_id"]).fetchone()[0]
    for row in rows:
        symbol = row["symbol"]
        shares = row["shares"]
        price = round((lookup(symbol))["price"], 2)
        total += price * shares
        stocks.append(
            {
                "symbol": symbol,
                "shares": shares,
                "price": float(price),
                "total_value": float(price * shares),
            }
        )

    return render_template("index.html", stocks=stocks, cash=cash, total=(total + cash))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        if not RequestValidator(request.form).validate_buy():
            if not BalanceValidator(request.form).validate_cash():
                return apology("you have not enough money to buy so many stocks")

            diff, cost, price = BalanceValidator(request.form).validate_cash()
            name = lookup(request.form.get("symbol"))["name"]

            data = {
                "symbol": request.form.get("symbol"),
                "stocks": request.form.get("shares"),
                "price": price,
                "cost": cost,
                "cash": diff,
                "total": (cost + diff),
                "name": name,
            }
            DBrequest().insert_transaction(
                data["symbol"],
                session["user_id"],
                data["stocks"],
                data["price"],
                -data["cost"],
            )
            DBrequest().update_user(diff, session["user_id"])
            return render_template("bought.html", data=data)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    rows = map(
        lambda x: list(x),
        DBrequest().select_all("transactions", session["user_id"]).fetchall(),
    )
    updated_rows = []
    for idx, row in enumerate(rows):
        transaction = "sale" if row[3] < 0 else "purchase"
        updated_row = {
            "id": row[0],
            "symbol": row[1],
            "amount": row[3],
            "price": float(row[4]),
            "cost": float(row[5]),
            "transaction": transaction,
            "date": row[6],
        }
        updated_rows.append(updated_row)
    print("rows:", updated_rows)
    return render_template("history.html", rows=updated_rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Forget any user_id
        session.clear()

        if not RequestValidator(request.form).validate_login():
            print("here 1")
            rows = DBrequest().select_username(request.form).fetchall()
            # Remember which user has logged in
            session["user_id"] = rows[0][0]

            # Redirect user to home page
            return redirect("/")

        # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        if request.form.get("symbol"):
            stock = lookup(request.form.get("symbol"))
            stock["price"] = float(stock["price"])
            if stock:
                return render_template("quoted.html", stock=stock)
            return render_template("quote.html")
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Ensure username was submitted
        if not RequestValidator(request.form).validate_register():

            password = request.form.get("password")
            password = generate_password_hash(
                password, method="pbkdf2:sha256", salt_length=8
            )

            DBrequest().insert_hash(request.form, password)

            # Redirect user to login page
            return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        if not RequestValidator(request.form).validate_sell(session["user_id"]):

            price = float((lookup(request.form.get("symbol")))["price"])
            cash = (DBrequest().select_cash(session["user_id"]))[0]["cash"]
            revenue = float(request.form.get("shares")) * price
            data = {
                "price": price,
                "name": lookup(request.form.get("symbol"))["name"],
                "symbol": request.form.get("symbol"),
                "stocks": request.form.get("shares"),
                "revenue": revenue,
                "cash": float(cash),
                "total": cash + revenue,
            }

            DBrequest().insert_transaction(
                request.form.get("symbol"),
                session["user_id"],
                (-int(request.form.get("shares"))),
                price,
                revenue,
            )
            DBrequest().update_user((cash + revenue), session["user_id"])

            return render_template("sold.html", data=data)
    else:
        return render_template("sell.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
