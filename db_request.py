import sqlite3 as SQL

# from cs50 import SQL

# Configure CS50 Library to use SQLite database
# db = SQL("sqlite:///finance.db")
con = SQL.connect("finance.db")
db = con.cursor()


class DBrequest:
    def select_cash(self, id):
        return db.execute("SELECT cash FROM users WHERE id=:id", dict(id=id))

    def select_index(self, id):
        return db.execute(
            "SELECT symbol, sum(amount) as shares FROM transactions WHERE userid=:id GROUP BY symbol HAVING shares > 0;",
            dict(id=id),
        )

    def select_symbol(self, id, form):
        print("form", form)
        return db.execute(
            "SELECT symbol, sum(amount) as shares FROM transactions WHERE userid=:id AND symbol=:symbol GROUP BY symbol;",
            dict(id=id, symbol=form.get("symbol")),
        )

    def select_username(self, form):
        return db.execute(
            "SELECT * FROM users WHERE username=:username;",
            dict(username=form.get("username")),
        )

    # def check_username(self, form):
    #     return db.execute(
    #         "SELECT COUNT(*) FROM users WHERE username=:username;",
    #         dict(username=form.get("username")),
    #     )

    def select_all(self, database, id):
        if database == "transactions":
            return db.execute(
                "SELECT * FROM transactions WHERE userid=:id ORDER BY date DESC;",
                dict(id=id),
            )
        if database == "users":
            return db.execute(
                "SELECT * FROM users WHERE userid=:id ORDER BY userid DESC;",
                dict(id=id),
            )

    def update_user(self, cash, id):
        return db.execute(
            "UPDATE users SET cash=:cash WHERE id=:id;", dict(cash=cash, id=id)
        )

    def insert_transaction(self, symbol, id, amount, price, cost):
        return db.execute(
            "INSERT INTO transactions (symbol, userid, amount, price, cost) VALUES (:symbol, :id, :amount, :price, :cost);",
            dict(symbol=symbol, id=id, amount=amount, price=price, cost=cost),
        )

    def insert_hash(self, form, hash):
        return db.execute(
            "INSERT INTO users (username, hash) VALUES (:username, :hash);",
            dict(username=form.get("username"), hash=hash),
        )
