# import sqlite3 as SQL

from cs50 import SQL

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")
# con = SQL.connect("finance.db")
# db = con.cursor()


class DBrequest:
    def select_cash(self, id):
        return db.execute("SELECT cash FROM users WHERE id=:id", id=id)

    def select_index(self, id):
        return db.execute(
            "SELECT symbol, sum(amount) as shares FROM transactions WHERE userid=:id GROUP BY symbol HAVING shares > 0;",
            id=id,
        )

    def select_symbol(self, id, symbol):
        return db.execute(
            "SELECT symbol, sum(amount) as shares FROM transactions WHERE userid=:id AND symbol=:symbol GROUP BY symbol;",
            id=id,
            symbol=symbol,
        )

    def select_username(self, username):
        return db.execute(
            "SELECT * FROM users WHERE username = :username;", username=username
        )

    def select_all(self, database, id):
        if database == "transactions":
            return db.execute(
                "SELECT * FROM transactions WHERE userid=:id ORDER BY date DESC;", id=id
            )
        if database == "users":
            return db.execute(
                "SELECT * FROM users WHERE userid=:id ORDER BY userid DESC;", id=id
            )

    def update_user(self, cash, id):
        return db.execute("UPDATE users SET cash=:cash WHERE id=:id;", cash=cash, id=id)

    def insert_transaction(self, symbol, id, amount, price, cost):
        return db.execute(
            "INSERT INTO transactions (symbol, userid, amount, price, cost) VALUES (:symbol, :id, :amount, :price, :cost);",
            symbol=symbol,
            id=id,
            amount=amount,
            price=price,
            cost=cost,
        )

    def insert_hash(self, username, hash):
        return db.execute(
            "INSERT INTO users (username, hash) VALUES (:username, :hash);",
            username=username,
            hash=hash,
        )
