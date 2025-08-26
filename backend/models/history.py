from sqlalchemy import Column, String, DateTime, CheckConstraint, ForeignKeyConstraint, Index, Text
from sqlalchemy.orm import relationship
from .database import Base
from typing import Dict, Optional
from datetime import datetime
import json

class History(Base):
    __tablename__ = "history"
    
    portfolio_id = Column(String(8), primary_key=True)
    date = Column(String(8), primary_key=True)
    time = Column(String(8), primary_key=True)
    seq_no = Column(String(4), primary_key=True)
    
    record_type = Column(String(2), CheckConstraint("record_type IN ('PT', 'PS', 'TR')"))
    action_code = Column(String(1), CheckConstraint("action_code IN ('A', 'C', 'D')"))
    before_image = Column(Text)
    after_image = Column(Text)
    reason_code = Column(String(4))
    
    process_date = Column(DateTime)
    process_user = Column(String(8))
    
    portfolio = relationship("Portfolio", back_populates="history_records")
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['portfolio_id'], 
            ['portfolios.port_id']
        ),
        Index('idx_history_portfolio_id', 'portfolio_id'),
        Index('idx_history_date', 'date'),
        Index('idx_history_record_type', 'record_type'),
        Index('idx_history_action_code', 'action_code'),
    )
    
    @classmethod
    def create_audit_record(cls, portfolio_id: str, record_type: str, action_code: str, 
                           before_data: Optional[Dict] = None, after_data: Optional[Dict] = None,
                           reason_code: str = "AUTO", user: str = "SYSTEM", db_session=None):
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M%S%f")[:8]
        
        seq_no = "0001"
        if db_session:
            existing_count = db_session.query(cls).filter(
                cls.portfolio_id == portfolio_id,
                cls.date == date_str,
                cls.time == time_str
            ).count()
            seq_no = f"{existing_count + 1:04d}"
        
        return cls(
            portfolio_id=portfolio_id,
            date=date_str,
            time=time_str,
            seq_no=seq_no,
            record_type=record_type,
            action_code=action_code,
            before_image=json.dumps(before_data) if before_data else None,
            after_image=json.dumps(after_data) if after_data else None,
            reason_code=reason_code,
            process_date=now,
            process_user=user
        )
    
    def get_before_data(self) -> Optional[Dict]:
        if self.before_image:
            try:
                return json.loads(self.before_image)
            except json.JSONDecodeError:
                return None
        return None
    
    def get_after_data(self) -> Optional[Dict]:
        if self.after_image:
            try:
                return json.loads(self.after_image)
            except json.JSONDecodeError:
                return None
        return None
    
    def to_dict(self) -> Dict:
        return {
            "portfolio_id": self.portfolio_id,
            "date": self.date,
            "time": self.time,
            "seq_no": self.seq_no,
            "record_type": self.record_type,
            "action_code": self.action_code,
            "before_data": self.get_before_data(),
            "after_data": self.get_after_data(),
            "reason_code": self.reason_code,
            "process_date": self.process_date.isoformat() if self.process_date else None,
            "process_user": self.process_user
        }
