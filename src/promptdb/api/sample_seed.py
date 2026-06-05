"""Self-seeding sample database (a synthetic bookshop — no real data).

Free-tier Render Postgres is reachable only on Render's internal network, so the sample is used
server-side only: the connection string never leaves the server, and the agent's SELECT-only
guardrail is what keeps it read-only. The server seeds it once on first use (idempotent).
"""

import os

from sqlalchemy import create_engine, text

_TABLES = [
    "CREATE TABLE IF NOT EXISTS author (id INT PRIMARY KEY, name TEXT, country TEXT)",
    "CREATE TABLE IF NOT EXISTS book (id INT PRIMARY KEY, title TEXT, author_id INT REFERENCES author(id), genre TEXT, price NUMERIC, published_year INT)",
    "CREATE TABLE IF NOT EXISTS customer (id INT PRIMARY KEY, name TEXT, city TEXT)",
    "CREATE TABLE IF NOT EXISTS book_order (id INT PRIMARY KEY, customer_id INT REFERENCES customer(id), order_date DATE)",
    "CREATE TABLE IF NOT EXISTS order_item (id INT PRIMARY KEY, order_id INT REFERENCES book_order(id), book_id INT REFERENCES book(id), quantity INT)",
]

_DATA = [
    "INSERT INTO author VALUES (1,'Ursula Vane','USA'),(2,'Idris Okafor','Nigeria'),(3,'Mei Lin','Singapore'),(4,'Tomas Reyes','Chile'),(5,'Anya Sokolova','Estonia')",
    "INSERT INTO book VALUES (1,'The Glass Tide',1,'SciFi',14.99,2019),(2,'Saltbound',1,'SciFi',12.50,2021),(3,'River of Names',2,'Literary',16.00,2018),(4,'The Lagos Codex',2,'Thriller',13.25,2022),(5,'Paper Moons',3,'Literary',11.00,2020),(6,'Quiet Machines',3,'SciFi',15.75,2023),(7,'Andes Light',4,'Travel',10.50,2017),(8,'The Salt Road',4,'Travel',12.00,2021),(9,'Winter Frequencies',5,'Mystery',13.99,2022),(10,'Amber Lines',5,'Mystery',9.99,2019),(11,'The Glass Tide II',1,'SciFi',15.99,2024),(12,'Northern Static',5,'Mystery',14.50,2024)",
    "INSERT INTO customer VALUES (1,'Dana K.','Austin'),(2,'Liam P.','Dublin'),(3,'Sara M.','Toronto'),(4,'Noah B.','Berlin'),(5,'Priya R.','Mumbai'),(6,'Eli T.','Lisbon'),(7,'Yuki S.','Osaka'),(8,'Omar F.','Cairo')",
    "INSERT INTO book_order VALUES (1,1,'2024-01-05'),(2,2,'2024-01-09'),(3,1,'2024-02-01'),(4,3,'2024-02-14'),(5,4,'2024-03-03'),(6,5,'2024-03-20'),(7,6,'2024-04-02'),(8,2,'2024-04-18'),(9,7,'2024-05-06'),(10,8,'2024-05-22'),(11,3,'2024-06-01'),(12,1,'2024-06-15')",
    "INSERT INTO order_item VALUES (1,1,1,2),(2,1,6,1),(3,2,3,1),(4,3,11,3),(5,4,5,2),(6,4,9,1),(7,5,4,1),(8,6,6,2),(9,7,2,1),(10,7,12,2),(11,8,1,1),(12,9,7,3),(13,10,10,1),(14,11,9,2),(15,11,3,1),(16,12,11,1),(17,12,6,1),(18,2,8,2),(19,5,2,1),(20,9,12,1)",
]

_cached_url: str | None = None


def ensure_seeded(admin_url: str) -> str:
    """Seed the bookshop if absent (idempotent). Returns the (server-side) connection URL."""
    eng = create_engine(admin_url, connect_args={"connect_timeout": 10})
    with eng.begin() as conn:
        if not conn.execute(text("SELECT to_regclass('public.book')")).scalar():
            for stmt in _TABLES + _DATA:
                conn.execute(text(stmt))
    eng.dispose()
    return admin_url


def sample_url() -> str | None:
    """Resolve the server-side sample URL, seeding on first use (cached). None if unconfigured."""
    global _cached_url
    if _cached_url:
        return _cached_url
    admin = os.environ.get("PROMPTDB_SAMPLE_ADMIN_URL")
    _cached_url = ensure_seeded(admin) if admin else os.environ.get("PROMPTDB_SAMPLE_DB_URL")
    return _cached_url
