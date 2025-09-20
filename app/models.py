from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timezone

Base = declarative_base()

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(String(500), nullable=False)
    issue = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<SupportTicket(id={self.id}, name='{self.name}', issue='{self.issue}')>"