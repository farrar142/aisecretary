from typing import Any, Iterable
from collections import deque


class FixedQueue[T](deque):
    @property
    def is_full(self):
        return self.max_len <= self.current_len

    def __init__(self, elements: Iterable[T], max_len: int):
        self.max_len = max_len
        self.current_len = 0
        super().__init__(elements)

    def append(self, item: T):
        if self.is_full:
            return
        self.current_len += 1
        super().append(item)

    def pop(self):
        element = super().pop()
        self.current_len -= 1
        return element

    def clear(self):
        super().clear()
        self.current_len = 0

    def remove(self, value: Any) -> None:
        try:
            super().remove(value)
            self.current_len -= 1
            return
        except Exception as e:
            raise e

    def insert(self, i: int, x: Any) -> None:
        raise

    def extend(self, iterable: Iterable) -> None:
        raise

    def extendleft(self, iterable: Iterable) -> None:
        raise
