"""Module for the Data models used by the APIRouter to define the request params"""

from pydantic import BaseModel


class UserQuery(BaseModel):
    query: str
    feature_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
