from typing import TypeVar
import uuid


T = TypeVar("T")
U = TypeVar("U")


def make_property(type_hint: type[T], default_value: U = None) -> T | U:
    field_name = str(uuid.uuid4())

    def getter(self):
        print("from make_property")
        if value := getattr(self, field_name, None):
            return value
        return default_value

    def setter(self, value: T):
        print("set value")
        setattr(self, field_name, value)
        return value

    return property(getter, setter)  # type:ignore
