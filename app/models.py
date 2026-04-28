from sqlalchemy import Column, Integer, Float, String, DateTime, Text, Index
from sqlalchemy.sql import func
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String(100), nullable=False)
    merchant = Column(String(200), nullable=False)
    transaction_date = Column(DateTime, nullable=False, index=True)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'transaction_date'),
        Index('idx_user_category', 'user_id', 'category'),
        Index('idx_user_merchant', 'user_id', 'merchant'),
    )
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "category": self.category,
            "merchant": self.merchant,
            "transaction_date": self.transaction_date.isoformat() if self.transaction_date else None
        }

class QueryHistory(Base):
    __tablename__ = "query_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    question = Column(Text, nullable=False)
    sql_generated = Column(Text, nullable=False)
    result_summary = Column(Text)
    result_count = Column(Integer, default=0)
    execution_time_ms = Column(Float)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question": self.question,
            "sql_generated": self.sql_generated,
            "result_summary": self.result_summary,
            "result_count": self.result_count,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }