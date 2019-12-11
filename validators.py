from helpers import apology
from db_request import DBrequest
from flask import request, session
from werkzeug import check_password_hash, generate_password_hash
from helpers import lookup


class RequestValidator:
    def __init__(self, form):
        self.form = form

    def validate_buy(self):
        # Ensure you can buy
        if not lookup(self.form.get("symbol")) or not self.form.get("symbol"):
            return apology("wrong symbol")

        elif not self.form.get("shares"):
            return apology("no number of shares")

        elif int(self.form.get("shares")) < 0:
            return apology("number of shares must be a positive integer")

        else:
            return None

    def validate_deposit(self):
        # Ensure you can deposit
        if not self.form.get("amount") or float(request.form.get("amount")) <= 0:
            return apology("wrong request")

        else:
            return None

    def validate_register(self):
        # Ensure you can register
        if not self.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not self.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password was confirmed
        elif not self.form.get("confirmation"):
            return apology("must confirm password", 403)

        elif not self.form.get("password") == self.form.get("confirmation"):
            return apology("password and confirmed password must be the same", 403)

        elif (
            len(DBrequest().select_username(self.form.get("username")).fetchall()) != 0
        ):
            return apology("Sorry, there is such username in our database", 403)

        else:
            return None

    def validate_login(self):
        # Ensure username was submitted
        if not self.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not self.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = DBrequest().select_username(self.form).fetchall()
        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], self.form["password"]):
            return apology("invalid username and/or password", 403)

        else:
            return None

    def validate_sell(self, id):
        # Ensure you can sell
        if not self.form.get("shares") or not self.form.get("symbol"):
            return apology("request incomplete")

        elif int(self.form.get("shares")) < 0:
            return apology("number of shares must be a positive integer")

        avaliable_shares = DBrequest().select_symbol(id, self.form)

        if len(avaliable_shares.fetchall()) == 0:
            return apology("you don't have such shares to sell")

        elif int(avaliable_shares[0][1]) < int(self.form.get("shares")):
            return apology("you don't have so many shares to sell")

        else:
            return None


class BalanceValidator:
    def __init__(self, form):
        self.form = form

    def validate_cash(self):
        cash = DBrequest().select_cash(session["user_id"]).fetchone()[0]
        price = round(float((lookup(self.form.get("symbol")))["price"]), 2)
        cost = float(self.form.get("shares")) * price
        diff = cash - cost

        if diff < 0:
            return None

        else:
            return diff, cost, price

