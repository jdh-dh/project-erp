from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChangeLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: int
    action: str
    changed_by: int
    changed_by_name: str
    changed_at: datetime
    before_data: dict | None
    after_data: dict | None
