import json
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.datastructures import MultiValueDict
from django.http import QueryDict

from dataclasses import dataclass, field, asdict
from enum import StrEnum
from typing import Optional, List, TypeVar, Generic, Dict, Any

T = TypeVar("T")


@dataclass
class IUserProfile:
    email: Optional[str] = None
    nick_name: Optional[str] = None
    provider_avatar_url: Optional[str] = None

@dataclass
class IResponseList(Generic[T]):
    total: int
    page: int
    pagesize: int
    data: List[T]

    def to_json(self) -> str:
        # Convert the instance to a dictionary and then serialize to JSON
        return json.dumps(asdict(self))

    def to_dict(self) -> Dict[Any, Any]:
        # Convert the instance to a dictionary and then serialize to JSON
        return asdict(self)


@dataclass
class IResponse(Generic[T]):
    data: T

    def to_json(self) -> str:
        # Convert the instance to a dictionary and then serialize to JSON
        return json.dumps(asdict(self))

    def to_dict(self) -> Dict[Any, Any]:
        # Convert the instance to a dictionary and then serialize to JSON
        return asdict(self)
