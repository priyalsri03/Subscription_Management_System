
import sqlite3

DATABASE = "database.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'customer'
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            product_type TEXT,
            sales_price REAL DEFAULT 0,
            cost_price REAL DEFAULT 0,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS product_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            variant_name TEXT,
            extra_price REAL DEFAULT 0,
            FOREIGN KEY(product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            billing_cycle TEXT NOT NULL,
            minimum_quantity INTEGER DEFAULT 1,
            start_date TEXT,
            end_date TEXT
        );

        CREATE TABLE IF NOT EXISTS quotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            validity_date TEXT,
            status TEXT DEFAULT 'Draft',
            FOREIGN KEY(customer_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_number TEXT UNIQUE,
            customer_id INTEGER,
            plan_id INTEGER,
            start_date TEXT,
            expiry_date TEXT,
            status TEXT DEFAULT 'Draft',
            FOREIGN KEY(customer_id) REFERENCES users(id),
            FOREIGN KEY(plan_id) REFERENCES plans(id)
        );

        CREATE TABLE IF NOT EXISTS discounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            discount_type TEXT,
            discount_value REAL,
            start_date TEXT,
            end_date TEXT,
            usage_limit INTEGER
        );

        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_id INTEGER,
            billing_period TEXT,
            total_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'Draft',
            UNIQUE(subscription_id, billing_period),
            FOREIGN KEY(subscription_id) REFERENCES subscriptions(id)
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            payment_method TEXT,
            amount REAL NOT NULL,
            payment_date TEXT,
            note TEXT,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id)
        );
    """)


# Add new discount fields to an existing database
    existing_columns = [
    row["name"]
    for row in conn.execute("PRAGMA table_info(discounts)").fetchall()
    ]

    new_columns = {
            "min_purchase": "REAL DEFAULT 0",
            "min_quantity": "INTEGER DEFAULT 1",
            "applies_to": "TEXT DEFAULT 'both'",
            "usage_count": "INTEGER DEFAULT 0"
        }

    for column, definition in new_columns.items():
            if column not in existing_columns:
                conn.execute(
                    f"ALTER TABLE discounts ADD COLUMN {column} {definition}"
                )


    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
