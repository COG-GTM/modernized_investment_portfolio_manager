from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class HistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    portfolio_id: str
    date: str
    time: str
    seq_no: str
    record_type: Optional[str] = None
    action_code: Optional[str] = None
    before_image: Optional[str] = None
    after_image: Optional[str] = None
    reason_code: Optional[str] = None
    process_date: Optional[datetime] = None
    process_user: Optional[str] = None
