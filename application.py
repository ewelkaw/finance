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


@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
  """Deposit money"""
  if request.method == "POST":
    if not request.form.get("amount") or float(request.form.get("amount"))<=0:
      return apology("wrong request")
    else:
      row = db.execute("SELECT cash FROM users WHERE id=:userid", userid=session["user_id"])
      money = round(row[0]["cash"] + float(request.form.get("amount")),2)
      db.execute("UPDATE users SET cash=:cash WHERE id=:userid", cash=money, userid=session["user_id"])
      data = {"cash": round(row[0]["cash"],2),
              "deposit": round(float(request.form.get("amount")),2),
              "current_cash": money,
              }
      return render_template("current_balance.html", data=data)
  else:
    return render_template("deposit.html")
  """Show portfolio of stocks"""


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    rows = db.execute("SELECT symbol, sum(amount) as shares FROM transactions WHERE userid= :user_id GROUP BY symbol", 
      user_id=session["user_id"])
    stocks = []
    total = 0
    print(rows)
    for row in rows:
      if int(row["shares"]) > 0:
        price = round((lookup(row["symbol"]))["price"],2)
        total += float(price) * row["shares"]
        stocks.append({
          "symbol": row["symbol"],
          "shares": row["shares"],
          "price": price, 
          "total": float(price) * row["shares"]
          })
    cash = round(db.execute("SELECT cash FROM users WHERE id= :user_id LIMIT 1", user_id=session["user_id"])[0]["cash"],2)
    total = round(total + db.execute("SELECT cash FROM users WHERE id= :user_id LIMIT 1", user_id=session["user_id"])[0]["cash"],2)
    
    return render_template("index.html", stocks=stocks, cash=cash, total=total)


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
  def __init__(self, connector, form):
    self.connector = connector
    self.form = form

  def validate_cash(self, cost):
    cash = self.connector.get_cash(session["user_id"])
    cash = round(float(cash[0]["cash"]),2)
    diff = round(cash - cost,2)
    if diff < 0:
      return apology("you have not enough money to buy so many stocks")
    else:
      return diff


class DbConnector():
  def __init__(self, db):
    self.db = db

  def get_cash(self, user_id):
    return db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=user_id)

  def buy(self, symbol, user_id, amount, cost, price):
    return db.execute("INSERT INTO transactions (symbol, userid, amount, price, cost) VALUES (:symbol, :userid, :amount, :price, :cost)", 
        symbol=symbol, userid=user_id, amount=amount, cost=cost, price=price)

  def set_cash(self, diff, user_id):
    db.execute("UPDATE users SET cash=:cash WHERE id=:userid", cash=diff, userid=user_id)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
      connector = DbConnector(db)
      validator = RequestValidator(form)
      balance_validator = BalanceValidator(form, connector)
      cost = round(float(self.form.get("shares")) * float((lookup(self.form.get("symbol")))["price"]),2)
      price = round(float((lookup(request.form.get("symbol")))["price"]),2))
      if not validator.validate_buy():
        return validator.validate_buy()
      if not balance_validator.validate_cash():
        return balance_validator.validate_cash()
      diff = balance_validator.validate_cash()
      data = {}
      bought = connector.buy(request.form.get("symbol"), session["user_id"], request.form.get("shares"), (-cost), price)
      
      data = {"name":   lookup(request.form.get("symbol"))["name"],
              "symbol": request.form.get("symbol"),
              "stocks": request.form.get("shares"),
              "price":  lookup(request.form.get("symbol"))["price"],
              "cost":   cost,
              "cash":   diff,
              "total":  (cost+diff),
      }
      return render_template("bought.html", data=data)
    else:
      return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    rows = db.execute("SELECT id, symbol, amount, price, cost, date FROM transactions WHERE userid=:userid ORDER BY date DESC", userid=session["user_id"])
    for row in rows:
      if row['amount'] < 0:
        row['transaction'] = "sale"
      else:
        row['transaction'] = "purchase"
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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

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
        
        rows = db.execute("SELECT * FROM users WHERE username = :username", 
          username=request.form.get("username"))
        
        if len(rows) != 0:
            return apology("Sorry, there is such username in our database", 403) 

        password = request.form.get("password")
        password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", 
          username=request.form.get("username"), hash=password)

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
      
      avaliable_shares = db.execute("SELECT sum(amount) as shares FROM transactions WHERE symbol=:symbol AND userid=:userid GROUP BY :symbol", 
        symbol=request.form.get("symbol"), userid=session["user_id"])
      if len(avaliable_shares) == 0:
         return apology("you don't have such shares to sell")
      elif int(avaliable_shares[0]["shares"]) < int(request.form.get("shares")):
        return apology("you don't have so many shares to sell")
      else:
        data = {}
        price = (lookup(request.form.get("symbol")))["price"]
        revenue = float(request.form.get("shares")) * price
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])
        cash = round(float(cash[0]["cash"]),2)
        sold = db.execute("INSERT INTO transactions (symbol, userid, amount, price, cost) VALUES (:symbol, :userid, :amount, :price, :revenue)", 
          symbol=request.form.get("symbol"), userid=session["user_id"], amount=(-int(request.form.get("shares"))), 
          revenue=revenue, price=price)
        db.execute("UPDATE users SET cash=:cash WHERE id=:userid", cash=(cash+revenue), userid=session["user_id"])
        data = {"name":   lookup(request.form.get("symbol"))["name"],
                "symbol": request.form.get("symbol"),
                "stocks": request.form.get("shares"),
                "price":  lookup(request.form.get("symbol"))["price"],
                "revenue":   revenue,
                "cash":   cash,
                "total": round(cash+revenue,2),
        }
        return render_template("sold.html", data=data)
    else:
      return render_template("sell.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
