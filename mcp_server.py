import sqlite3
from mcp.server.fastmcp import FastMCP
import os
# Create MCP server
mcp = FastMCP("banking_mcp_server")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bank_data.db")

def get_db_connection():
    """Create database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

@mcp.tool()
def get_last_transaction(customer_id: str, account_type: str) -> dict:
    """
    Get the most recent transaction for a customer's account.
    
    Args:
        customer_id: The customer's ID (e.g., 'user123')
        account_type: Account type ('checking' or 'savings')
    
    Returns:
        dict: The most recent transaction details
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT date, description, amount, currency
        FROM transactions
        WHERE customer_id = ? AND account_type = ?
        ORDER BY date DESC, id DESC
        LIMIT 1
    """, (customer_id, account_type))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "status": "ok",
            "customer_id": customer_id,
            "account_type": account_type,
            "date": row["date"],
            "description": row["description"],
            "amount": row["amount"],
            "currency": row["currency"]
        }
    else:
        return {
            "status": "error",
            "message": f"No transactions found for {customer_id} - {account_type}"
        }

@mcp.tool()
def get_recent_transactions(customer_id: str, account_type: str, limit: int = 5) -> dict:
    """
    Get recent transactions for a customer's account.
    
    Args:
        customer_id: The customer's ID (e.g., 'user123')
        account_type: Account type ('checking' or 'savings')
        limit: Number of transactions to return (1-10)
    
    Returns:
        dict: List of recent transactions
    """
    # Validate limit
    if limit < 1:
        limit = 1
    if limit > 10:
        limit = 10
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT date, description, amount, currency
        FROM transactions
        WHERE customer_id = ? AND account_type = ?
        ORDER BY date DESC, id DESC
        LIMIT ?
    """, (customer_id, account_type, limit))
    
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        transactions = []
        for row in rows:
            transactions.append({
                "date": row["date"],
                "description": row["description"],
                "amount": row["amount"],
                "currency": row["currency"]
            })
        
        return {
            "status": "ok",
            "customer_id": customer_id,
            "account_type": account_type,
            "count": len(transactions),
            "transactions": transactions
        }
    else:
        return {
            "status": "error",
            "message": f"No transactions found for {customer_id} - {account_type}"
        }

@mcp.tool()
def calculate_account_balance(customer_id: str, account_type: str) -> dict:
    """
    Calculate current account balance from all transactions.
    
    Args:
        customer_id: The customer's ID (e.g., 'user123')
        account_type: Account type ('checking' or 'savings')
    
    Returns:
        dict: Current balance details
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT SUM(amount) as total
        FROM transactions
        WHERE customer_id = ? AND account_type = ?
    """, (customer_id, account_type))
    
    row = cursor.fetchone()
    conn.close()
    
    # Get the total (will be None if no transactions)
    balance = row["total"] if row["total"] is not None else 0.0
    
    return {
        "status": "ok",
        "customer_id": customer_id,
        "account_type": account_type,
        "balance": float(balance),
        "currency": "USD"
    }
@mcp.tool()
def get_transactions_by_date(customer_id: str, account_type: str, date: str) -> dict:
    """
    Get transactions for a specific date.
    
    Args:
        customer_id: The customer's ID (e.g., 'user123')
        account_type: Account type ('checking' or 'savings')
        date: Date in format 'YYYY-MM-DD' (e.g., '2026-01-09')
    
    Returns:
        dict: Transactions for that date
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT date, description, amount, currency
        FROM transactions
        WHERE customer_id = ? AND account_type = ? AND date = ?
        ORDER BY id DESC
    """, (customer_id, account_type, date))
    
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        transactions = []
        for row in rows:
            transactions.append({
                "date": row["date"],
                "description": row["description"],
                "amount": row["amount"],
                "currency": row["currency"]
            })
        
        return {
            "status": "ok",
            "customer_id": customer_id,
            "account_type": account_type,
            "date": date,
            "count": len(transactions),
            "transactions": transactions
        }
    else:
        return {
            "status": "error",
            "message": f"No transactions found for {customer_id} on {date} in {account_type} account"
        }

if __name__ == "__main__":
    
    mcp.run()