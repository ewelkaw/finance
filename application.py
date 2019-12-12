from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import werkzeug

from validators import RequestValidator, BalanceValidator
from helpers import login_required, lookup, usd
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
        if RequestValidator(request.form).validate_deposit():
            row = DBrequest().select_cash(session["user_id"])
            cash = round(row[0]["cash"], 2)
            deposit = round(float(request.form.get("amount")), 2)
            new_cash = cash + deposit

            DBrequest().update_user(new_cash, session["user_id"])
            data = {
                "cash": cash,
                "deposit": deposit,
                "current_cash": new_cash,
            }
            return render_template("current_balance.html", data=data)
        else:
            return render_template("deposit_again.html")
    else:
        return render_template("deposit.html")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    rows = DBrequest().select_index(session["user_id"])
    stocks = []
    total = 0
    cash = float(DBrequest().select_cash(session["user_id"])[0]["cash"])

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
        if RequestValidator(request.form).validate_buy():
            if not BalanceValidator(request.form).validate_cash():
                return render_template("buy_again.html")

            diff, cost, price = BalanceValidator(request.form).validate_cash()
            symbol = request.form.get("symbol")
            if not symbol:
                return render_template("buy.html")
            symbol_name = lookup(symbol)["symbol"]

            data = {
                "symbol": symbol_name,
                "stocks": request.form.get("shares"),
                "price": price,
                "cost": cost,
                "cash": diff,
                "total": (cost + diff),
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
            return render_template("buy_again.html")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    rows = DBrequest().select_all("transactions", session["user_id"])

    for row in rows:
        if row["amount"] < 0:
            row["transaction"] = "sale"
        else:
            row["transaction"] = "purchase"
        row["price"] = float(row["price"])
        row["cost"] = float(row["cost"])
    return render_template("history.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Forget any user_id
        session.clear()

        if RequestValidator(request.form).validate_login():
            rows = DBrequest().select_username(request.form.get("username"))

            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]

            # Redirect user to home page
            return redirect("/")
        else:
            return render_template("login_again.html")

        # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return render_template("login.html")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        if request.form.get("symbol") and request.form.get("symbol") != "0":
            stock = lookup(request.form.get("symbol"))
            stock["price"] = float(stock["price"])
            if stock:
                return render_template("quoted.html", stock=stock)
            return render_template("quote.html")
        else:
            return render_template("quote.html")
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Ensure username was submitted
        if RequestValidator(request.form).validate_register():

            password = request.form.get("password")
            password = generate_password_hash(
                password, method="pbkdf2:sha256", salt_length=8
            )

            DBrequest().insert_hash(request.form.get("username"), password)

            # Redirect user to login page
            return redirect("/login")
        else:
            return render_template("register_again.html")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        if RequestValidator(request.form).validate_sell(session["user_id"]):
            symbol = request.form.get("symbol")
            price = float((lookup(symbol))["price"])
            cash = (DBrequest().select_cash(session["user_id"]))[0]["cash"]
            revenue = float(request.form.get("shares")) * price
            data = {
                "price": price,
                "symbol": symbol,
                "stocks": request.form.get("shares"),
                "revenue": revenue,
                "cash": float(cash),
                "total": cash + revenue,
            }

            DBrequest().insert_transaction(
                symbol,
                session["user_id"],
                (-int(request.form.get("shares"))),
                price,
                revenue,
            )
            DBrequest().update_user((cash + revenue), session["user_id"])

            return render_template("sold.html", data=data)
        else:
            return render_template("sell_again.html")
    else:
        return render_template("sell.html")
