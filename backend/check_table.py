import sqlite3, pathlib

db = pathlib.Path(__file__).resolve().parent.parent / 'data' / 'stock_data.db'
with sqlite3.connect(db) as con:
    cur = con.execute("PRAGMA table_info(closing_price);")
    for cid, name, typ, notnull, default, pk in cur:
        print(cid, name, typ, "PK=" + str(pk))