"""
Pydantic v1 / v2 compatibility utilities.
"""

from typing import Type, TypeVar, Any, Dict
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    import json
    return json.loads(model.json())


def model_from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
    if hasattr(cls, "model_validate"):
        return cls.model_validate(data)
    return cls.parse_obj(data)


def model_from_json(cls: Type[T], json_str: str) -> T:
    if hasattr(cls, "model_validate_json"):
        return cls.model_validate_json(json_str)
    return cls.parse_raw(json_str)


def model_schema(cls: Type[BaseModel]) -> Dict[str, Any]:
    if hasattr(cls, "model_json_schema"):
        return cls.model_json_schema()
    return cls.schema()


def model_construct(cls: Type[T], **kwargs) -> T:
    if hasattr(cls, "model_construct"):
        return cls.model_construct(**kwargs)
    return cls.construct(**kwargs)
