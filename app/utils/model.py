
from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, Optional, Any
from datetime import datetime


class UrlsPayload(BaseModel):
    url: list[str]


class BaseResult(BaseModel):
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M")
        }
    )

    url: Optional[str] = None
    plugin: Optional[str] = None
    content_type: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    error: Optional[str] = None
    links: Optional[tuple[str, ...]] = None

    def _replace(self, **kwargs):
        return self.model_copy(update=kwargs)


class FullResult(BaseResult):
    data: Optional[Dict[str, Any]] = None

    def _replace(self, **kwargs):
        return self.model_copy(update=kwargs)


class TxtResult(BaseResult):
    text: Optional[str] = None

    def _replace(self, **kwargs):
        return self.model_copy(update=kwargs)