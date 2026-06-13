
from pydantic import BaseModel, ConfigDict, Field
from typing import Dict, Optional, Any
from datetime import datetime
from httpx import Response
from ..utils import get_parsed_url, parse_content_type


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
    status_code: Optional[int] = None

    def _replace(self, **kwargs):
        return self.model_copy(update=kwargs)

    @classmethod
    def build_from_response(cls, r: Response):
        return cls(
            url=get_parsed_url(str(r.url)),
            content_type=parse_content_type(r.headers.get('content-type')),
            status_code=r.status_code
        )


class TxtResult(BaseResult):
    text: Optional[str] = None
