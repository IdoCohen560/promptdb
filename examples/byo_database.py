"""Query your own database — build a throwaway store DB and ask it questions read-only.

This is the own-DB path: point PROMPTDB_DATABASE_URL at any SQLAlchemy URL and the agent runs
against it. Nothing here touches the bundled Chinook sample.

Run from the repo root (ANTHROPIC_API_KEY set, or PROMPTDB_PROVIDER=ollama for a local model):
    python examples/byo_database.py
"""

import os
import sqlite3
import tempfile

# 1) build a tiny "user database"
db = os.path.join(tempfile.mkdtemp(), "mystore.db")
con = sqlite3.connect(db)
con.executescript(
    """
    CREATE TABLE product (id INTEGER PRIMARY KEY, name TEXT, price REAL);
    CREATE TABLE sale (id INTEGER PRIMARY KEY, product_id INTEGER REFERENCES product(id), qty INTEGER);
    INSERT INTO product VALUES (1,'Widget',9.99),(2,'Gadget',19.50),(3,'Gizmo',4.25);
    INSERT INTO sale VALUES (1,1,10),(2,2,3),(3,1,5),(4,3,20);
    """
)
con.commit()
con.close()

# 2) point the agent at it BEFORE importing the graph (the engine reads this at first use)
os.environ["PROMPTDB_DATABASE_URL"] = f"sqlite:///{db}"

from promptdb.agent.graph import build_graph  # noqa: E402

result = build_graph().invoke({"question": "which product earned the most total revenue?"})
print("SQL:", result.get("sql"))
print("Answer:", result.get("answer"))
print(f"Cost: ${result.get('cost_usd', 0):.5f}")
