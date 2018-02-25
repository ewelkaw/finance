sqlite3 finance.db
#sqlite >>> .schema

CREATE TABLE 'users' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'username' TEXT NOT NULL, 'hash' TEXT NOT NULL, 'cash' NUMERIC NOT NULL DEFAULT 10000.00 );
CREATE UNIQUE INDEX 'username' ON "users" ("username");

CREATE TABLE 'transactions' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'symbol' TEXT NOT NULL,  'userid' NUMERIC NOT NULL, 'amount' NUMERIC NOT NULL, 'price' NUMERIC NOT NULL, 'cost' NUMERIC NOT NULL, 'date' TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
CREATE UNIQUE INDEX 'id' ON "transactions" ("id");

, CASE WHEN amount < 0 THEN 'sell'
      WHEN amount > 0 THEN 'purchase' END transaction