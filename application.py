import sqlite3 as SQL
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash
import werkzeug

from helpers import apology, login_required, lookup, usd

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

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")
# con = SQL.connect("finance.db")
# db = con.cursor()

class DBrequest:

  def select_cash(self, id):
    return db.execute("SELECT cash FROM users WHERE id=:id", id=id)

  def select_index(self, id):
    return db.execute("SELECT symbol, sum(amount) as shares FROM transactions WHERE userid=:id GROUP BY symbol HAVING shares > 0;", id=id)

  def select_symbol(self, id, symbol):
    return db.execute("SELECT symbol, sum(amount) as shares FROM transactions WHERE userid=:id AND symbol=:symbol GROUP BY symbol;", id=id, symbol=symbol)

  def select_username(self, username):
    return db.execute("SELECT * FROM users WHERE username = :username;", username=username)

  def select_all(self, database, id):
    if database == "transactions":
      return db.execute("SELECT * FROM transactions WHERE userid=:id ORDER BY date DESC;", id=id)
    if database == "users":
      return db.execute("SELECT * FROM users WHERE userid=:id ORDER BY userid DESC;", id=id)

  def update_user(self, cash, id):
    return db.execute("UPDATE users SET cash=:cash WHERE id=:id;", cash=cash, id=id)

  def insert_transaction(self, symbol, id, amount, price, cost):
    return db.execute("INSERT INTO transactions (symbol, userid, amount, price, cost) VALUES (:symbol, :id, :amount, :price, :cost);", 
        symbol=symbol, id=id, amount=amount, price=price, cost=cost)

  def insert_hash(self, username, hash):
     return db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash);", username=username, hash=hash)


class RequestValidator():
  def __init__(self, form):
    self.form = form

  def validate_buy(self):
    if not lookup(self.form.get("symbol")) or not self.form.get("symbol"):
      return apology("wrong symbol")
    elif not self.form.get("shares"):
      return apology("no number of shares")
    elif int(self.form.get("shares")) < 0:
      return apology("number of shares must be a positive integer")
    else:
      return None

class BalanceValidator():
  def __init__(self, form):
    self.form = form

  def validate_cash(self):
    cash = (DBrequest().select_cash(session["user_id"]))[0]["cash"]
    price = round(float((lookup(self.form.get("symbol")))["price"]),2)
    cost = float(self.form.get("shares")) * price
    diff = cash - cost
    if diff < 0:
      return None
    else:
      return diff, cost, price


@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
  """Deposit money"""
  if request.method == "POST":
    if not request.form.get("amount") or float(request.form.get("amount"))<=0: 
      return apology("wrong request")
    else:
      row = DBrequest().select_cash(session["user_id"])
      cash = round(row[0]["cash"],2)
      deposit = round(float(request.form.get("amount")),2)
      new_cash = (cash + deposit)
      DBrequest().update_user(new_cash, session["user_id"])
      data = {"cash": cash,
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
    print(rows)
    for row in rows:
      symbol = row["symbol"]
      shares = row["shares"]
      price = round((lookup(symbol))["price"],2)
      total += price * shares
      stocks.append({
        "symbol": symbol,
        "shares": shares,
        "price": float(price), 
        "total_value": float(price * shares),
          })
    cash = float(DBrequest().select_cash(session["user_id"])[0]["cash"])
    total = total + cash

    return render_template("index.html", stocks=stocks, cash=cash, total=total)


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

      data = {"symbol": request.form.get("symbol"),
              "stocks": request.form.get("shares"),
              "price":  price,
              "cost":   cost,
              "cash":   diff,
              "total":  (cost+diff),
              "name": name,
      }
      DBrequest().insert_transaction(data["symbol"], session["user_id"], data["stocks"], data["price"], -data["cost"])  
      DBrequest().update_user(diff, session["user_id"])
      return render_template("bought.html", data=data)
    else:
      return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    rows = DBrequest().select_all("transactions", session["user_id"])

    for row in rows:
      if row['amount'] < 0:
        row['transaction'] = "sale"
      else:
        row['transaction'] = "purchase"
      row["price"] = float(row["price"])
      row["cost"] = float(row["cost"])
    return render_template("history.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = DBrequest().select_username(request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

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
        if stock:
          return render_template("quoted.html", stock=stock)
        return render_template("quote.html")
    else:
      return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)
        
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)
        
        # Ensure password was confirmed
        elif not request.form.get("confirmation"):
            return apology("must confirm password", 403)
        
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("password and confirmed password must be the same", 403)
        
        rows = DBrequest().select_username(request.form.get("username"))
        
        if len(rows) != 0:
            return apology("Sorry, there is such username in our database", 403) 

        password = request.form.get("password")
        password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        DBrequest().insert_hash(request.form.get("username"), password)

        # Redirect user to login page
        return redirect("/login")        

    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
      if not request.form.get("shares") or not request.form.get("symbol"):
        return apology("request incomplete")
      elif int(request.form.get("shares")) < 0:
        return apology("number of shares must be a positive integer")
      
      avaliable_shares = DBrequest().select_symbol(session["user_id"], request.form.get("symbol"))

      if len(avaliable_shares) == 0:
         return apology("you don't have such shares to sell")
      
      elif int(avaliable_shares[0]["shares"]) < int(request.form.get("shares")):
        return apology("you don't have so many shares to sell")
      else:
        price = float((lookup(request.form.get("symbol")))["price"])
        cash = (DBrequest().select_cash(session["user_id"]))[0]["cash"]
        revenue = float(request.form.get("shares")) * price
        data = {"price": price,
                "name":   lookup(request.form.get("symbol"))["name"],
                "symbol": request.form.get("symbol"),
                "stocks": request.form.get("shares"),
                "revenue": revenue,
                "cash": float(cash),
                "total": cash+revenue,
        }
        DBrequest().insert_transaction(request.form.get("symbol"), session["user_id"], (-int(request.form.get("shares"))), price, revenue)
        DBrequest().update_user((cash+revenue), session["user_id"])

        return render_template("sold.html", data=data)
    else:
      return render_template("sell.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
