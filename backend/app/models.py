from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=1, max_length=200)
    done: bool | None = None


class TaskOut(BaseModel):
    id: str
    title: str
    done: bool
    created_at: datetime
