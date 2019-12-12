from db_request import DBrequest
from flask import request, session, render_template
from werkzeug import check_password_hash, generate_password_hash
from helpers import lookup


class RequestValidator:
    def __init__(self, form):
        self.form = form

    def validate_buy(self):
        # Ensure you can buy
        if not lookup(self.form.get("symbol")) or not self.form.get("symbol"):
            return False

        elif not self.form.get("shares"):
            return False

        elif int(self.form.get("shares")) < 0:
            return False

        else:
            return True

    def validate_deposit(self):
        # Ensure you can deposit
        if not self.form.get("amount") or float(request.form.get("amount")) <= 0:
            return False

        else:
            return True

    def validate_register(self):
        # Ensure you can register
        if not self.form.get("username"):
            return False

        # Ensure password was submitted
        elif not self.form.get("password"):
            return False

        # Ensure password was confirmed
        elif not self.form.get("confirmation"):
            return False

        elif not self.form.get("password") == self.form.get("confirmation"):
            return False

        elif len(DBrequest().select_username(self.form.get("username"))) != 0:
            return False

        else:
            return True

    def validate_login(self):
        # Ensure username was submitted
        if not self.form.get("username"):
            return False

        # Ensure password was submitted
        elif not self.form.get("password"):
            return False

        # Query database for username
        rows = DBrequest().select_username(self.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], self.form.get("password")
        ):
            return False

        else:
            return True

    def validate_sell(self, id):
        # Ensure you can sell
        if (
            not self.form.get("shares")
            or not self.form.get("symbol")
            or self.form.get("symbol") == "0"
        ):
            return False

        elif int(self.form.get("shares")) < 0:
            return False

        avaliable_shares = DBrequest().select_symbol(id, self.form.get("symbol"))
        if len(avaliable_shares) == 0:
            return False

        elif int(avaliable_shares[0]["shares"]) < int(self.form.get("shares")):
            return False

        else:
            return True


class BalanceValidator:
    def __init__(self, form):
        self.form = form

    def validate_cash(self):
        cash = (DBrequest().select_cash(session["user_id"]))[0]["cash"]
        price = round(float((lookup(self.form.get("symbol")))["price"]), 2)
        cost = float(self.form.get("shares")) * price
        diff = cash - cost

        if diff < 0:
            return False

        else:
            return diff, cost, price

