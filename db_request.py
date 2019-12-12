from cs50 import SQL
from pathlib import Path

# Configure CS50 Library to use SQLite database
FINANCE_DB = Path(__file__).parent.absolute().joinpath("finance.db")
if not FINANCE_DB.exists():
    FINANCE_DB.touch()
db = SQL("sqlite:///finance.db")


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


if __name__ == "__main__":
    print("Database is cleaned and prepared...")
    db.execute("DROP TABLE IF EXISTS users;")
    db.execute("DROP TABLE IF EXISTS transactions;")
    db.execute(
        "CREATE TABLE 'users' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'username' TEXT NOT NULL, 'hash' TEXT NOT NULL, 'cash' NUMERIC NOT NULL DEFAULT 10000.00 );"
    )
    db.execute(
        "CREATE TABLE 'transactions' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'symbol' TEXT NOT NULL,  'userid' NUMERIC NOT NULL, 'amount' NUMERIC NOT NULL, 'price' NUMERIC NOT NULL, 'cost' NUMERIC NOT NULL, 'date' TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
    )
