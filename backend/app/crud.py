from sqlalchemy.orm import Session
from models import SupportTicket
from typing import Optional
from datetime import datetime, timezone

ISSUE_TYPES = {
    "wifi_not_working": {"description": "Wi-Fi not working", "price": 20.0},
    "email_login_issues": {"description": "Email login issues - password reset", "price": 15.0},
    "slow_laptop": {"description": "Slow laptop performance - CPU change", "price": 25.0},
    "printer_problems": {"description": "Printer problems - power plug change", "price": 10.0}
}

def get_issue_price(issue_type: str) -> float:
    """Get price for a specific issue type"""
    return ISSUE_TYPES.get(issue_type, {}).get("price", 0.0)

def get_issue_description(issue_type: str) -> str:
    """Get description for a specific issue type"""
    return ISSUE_TYPES.get(issue_type, {}).get("description", "Unknown issue")

def create_ticket(
    db: Session,
    name: str,
    email: str,
    phone: str,
    address: str,
    issue: str,
    price: float
) -> SupportTicket:
    """Create a new support ticket"""
    db_ticket = SupportTicket(
        name=name,
        email=email,
        phone=phone,
        address=address,
        issue=issue,
        price=price,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def edit_ticket(
    db: Session,
    ticket_id: int,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    issue: Optional[str] = None,
    price: Optional[float] = None
) -> Optional[SupportTicket]:
    """Edit an existing support ticket"""
    db_ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not db_ticket:
        return None
    
    if name is not None:
        db_ticket.name = name
    if email is not None:
        db_ticket.email = email
    if phone is not None:
        db_ticket.phone = phone
    if address is not None:
        db_ticket.address = address
    if issue is not None:
        db_ticket.issue = issue
    if price is not None:
        db_ticket.price = price
    
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def get_ticket(db: Session, ticket_id: int) -> Optional[SupportTicket]:
    """Get a support ticket by ID"""
    return db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()

def get_all_tickets(db: Session, skip: int = 0, limit: int = 100):
    """Get all support tickets"""
    return db.query(SupportTicket).offset(skip).limit(limit).all()