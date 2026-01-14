import sqlite3
import os

def create_database():
    """Create SQLite database with customers and transactions tables."""
    
    
    db_path = "bank_data.db"
    
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
  
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
   
    cursor.execute("""
        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT
        )
    """)
    
   
    cursor.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT NOT NULL,
            account_type TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'USD',
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)
    
   
    cursor.execute("""
        INSERT INTO customers (customer_id, name, email)
        VALUES ('user123', 'John Doe', 'john@example.com')
    """)
    
   
    checking_transactions = [
        ('user123', 'checking', '2026-01-09', 'Grocery Store', -42.30),
        ('user123', 'checking', '2026-01-09', 'Salary', 2500.00),
        ('user123', 'checking', '2026-01-08', 'Coffee Shop', -3.80),
        ('user123', 'checking', '2026-01-07', 'Internet Bill', -55.00),
        ('user123', 'checking', '2026-01-06', 'Restaurant', -45.20),
    ]
    
    for trans in checking_transactions:
        cursor.execute("""
            INSERT INTO transactions (customer_id, account_type, date, description, amount)
            VALUES (?, ?, ?, ?, ?)
        """, trans)
   
    savings_transactions = [
        ('user123', 'savings', '2026-01-06', 'Interest', 4.12),
        ('user123', 'savings', '2026-01-03', 'Transfer from Checking', 200.00),
        ('user123', 'savings', '2025-12-28', 'Deposit', 500.00),
    ]
    
    for trans in savings_transactions:
        cursor.execute("""
            INSERT INTO transactions (customer_id, account_type, date, description, amount)
            VALUES (?, ?, ?, ?, ?)
        """, trans)
    
    #
    conn.commit()
    conn.close()
    
    print(f" Database created: {db_path}")
    print(f" Sample customer: user123")
    print(f" Transactions added: {len(checking_transactions) + len(savings_transactions)}")

if __name__ == "__main__":
    create_database()