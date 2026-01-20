# Contoso Customer Service MCP Server
# Run with: cd mcp && uv run mcp_server.py

from fastmcp import FastMCP
from typing import List, Optional
from pydantic import BaseModel, Field
import sqlite3
import asyncio
from datetime import datetime

mcp = FastMCP(
    name="Contoso Customer Service",
    instructions=(
        "This MCP server provides tools for customer service operations. "
        "Use these tools to look up customers, check billing, and manage support tickets."
    ),
)

DB_PATH = "contoso.db"


def get_db() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


##############################################################################
#                              Pydantic MODELS                               #
##############################################################################

class Customer(BaseModel):
    """Basic customer information"""
    customer_id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    loyalty_level: str


class BillingSummary(BaseModel):
    """Customer billing overview"""
    customer_id: int
    total_due: float
    invoices: List[dict]


class SupportTicket(BaseModel):
    """Support ticket information"""
    ticket_id: int
    customer_id: int
    subject: str
    description: str
    status: str
    priority: str
    opened_at: str
    closed_at: Optional[str] = None


##############################################################################
#                               TOOL ENDPOINTS                               #
##############################################################################

@mcp.tool(description="List all customers in the system")
def list_customers() -> List[Customer]:
    """Returns a list of all customers with their basic information."""
    db = get_db()
    rows = db.execute(
        "SELECT customer_id, first_name, last_name, email, phone, loyalty_level FROM Customers"
    ).fetchall()
    db.close()
    return [Customer(**dict(r)) for r in rows]


@mcp.tool(description="Get detailed information for a specific customer by their ID")
def get_customer(customer_id: int) -> Customer:
    """Look up a single customer by their ID."""
    db = get_db()
    row = db.execute(
        "SELECT customer_id, first_name, last_name, email, phone, loyalty_level "
        "FROM Customers WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()
    db.close()
    if not row:
        raise ValueError(f"Customer {customer_id} not found")
    return Customer(**dict(row))


@mcp.tool(description="Get billing summary showing what a customer owes")
def get_billing_summary(customer_id: int) -> BillingSummary:
    """Returns the total amount due and list of outstanding invoices for a customer."""
    db = get_db()
    
    # Check customer exists
    cust = db.execute(
        "SELECT 1 FROM Customers WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    if not cust:
        db.close()
        raise ValueError(f"Customer {customer_id} not found")
    
    # Get invoices with payment totals
    inv_rows = db.execute(
        """
        SELECT inv.invoice_id, inv.amount, inv.due_date,
               IFNULL(SUM(pay.amount), 0) AS paid
        FROM Invoices inv
        LEFT JOIN Payments pay ON pay.invoice_id = inv.invoice_id
                                 AND pay.status = 'successful'
        WHERE inv.subscription_id IN
            (SELECT subscription_id FROM Subscriptions WHERE customer_id = ?)
        GROUP BY inv.invoice_id
        """,
        (customer_id,),
    ).fetchall()
    db.close()
    
    invoices = [
        {
            "invoice_id": r["invoice_id"],
            "amount": r["amount"],
            "paid": r["paid"],
            "outstanding": max(r["amount"] - r["paid"], 0.0),
            "due_date": r["due_date"]
        }
        for r in inv_rows
    ]
    total_due = sum(inv["outstanding"] for inv in invoices)
    
    return BillingSummary(
        customer_id=customer_id,
        total_due=total_due,
        invoices=invoices
    )


@mcp.tool(description="Get support tickets for a customer, optionally filtered to open tickets only")
def get_support_tickets(customer_id: int, open_only: bool = False) -> List[SupportTicket]:
    """Returns support tickets for a customer."""
    db = get_db()
    
    query = """
        SELECT ticket_id, customer_id, subject, description, status, 
               priority, opened_at, closed_at
        FROM SupportTickets 
        WHERE customer_id = ?
    """
    if open_only:
        query += " AND status != 'closed'"
    query += " ORDER BY opened_at DESC"
    
    rows = db.execute(query, (customer_id,)).fetchall()
    db.close()
    return [SupportTicket(**dict(r)) for r in rows]


@mcp.tool(description="Create a new support ticket for a customer")
def create_support_ticket(
    customer_id: int,
    subject: str,
    description: str,
    priority: str = "medium"
) -> SupportTicket:
    """Creates a new support ticket and returns the created ticket."""
    # Validate priority
    if priority not in ["low", "medium", "high"]:
        raise ValueError("Priority must be 'low', 'medium', or 'high'")
    
    opened_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    db = get_db()
    
    # Verify customer exists
    cust = db.execute(
        "SELECT 1 FROM Customers WHERE customer_id = ?", (customer_id,)
    ).fetchone()
    if not cust:
        db.close()
        raise ValueError(f"Customer {customer_id} not found")
    
    # Get first subscription for the customer (simplified)
    sub = db.execute(
        "SELECT subscription_id FROM Subscriptions WHERE customer_id = ? LIMIT 1",
        (customer_id,)
    ).fetchone()
    subscription_id = sub["subscription_id"] if sub else None
    
    cur = db.execute(
        """
        INSERT INTO SupportTickets
        (customer_id, subscription_id, category, opened_at, closed_at,
         status, priority, subject, description, cs_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            customer_id,
            subscription_id,
            "general",
            opened_at,
            None,
            "open",
            priority,
            subject,
            description,
            "AI_Agent",
        ),
    )
    ticket_id = cur.lastrowid
    db.commit()
    
    row = db.execute(
        "SELECT ticket_id, customer_id, subject, description, status, "
        "priority, opened_at, closed_at FROM SupportTickets WHERE ticket_id = ?",
        (ticket_id,)
    ).fetchone()
    db.close()
    
    return SupportTicket(**dict(row))


##############################################################################
#                                RUN SERVER                                  #
##############################################################################
if __name__ == "__main__":
    print("\n" + "="*60)
    print("Contoso Customer Service MCP Server")
    print("="*60)
    print("\nAvailable tools:")
    print("  - list_customers: List all customers")
    print("  - get_customer: Get a specific customer by ID")
    print("  - get_billing_summary: Check what a customer owes")
    print("  - get_support_tickets: View customer's support tickets")
    print("  - create_support_ticket: Create a new support ticket")
    print("\n" + "="*60 + "\n")
    
    asyncio.run(mcp.run_http_async(port=8000))
