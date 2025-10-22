"""Module for the Data models used by the APIRouter to define the request params"""

from pydantic import BaseModel


class UserQuery(BaseModel):
    query: str
