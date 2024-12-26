import queue
import threading
from functools import wraps
from typing import Callable, Generic, ParamSpec, TypeVar
from returns.result import safe, Result

P = ParamSpec("P")
T = TypeVar("T")


class Thread(Generic[P, T]):
    def __init__(self, function: Callable[P, T], *args: P.args, **kwargs: P.kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.queue = queue.Queue[Result[T, Exception]]()
        self.thread = threading.Thread(target=self.run_with_result)
        self.thread.start()

    def run_with_result(self):
        @safe
        def inner():
            return self.function(*self.args, **self.kwargs)

        self.queue.put(inner())

    def join(self) -> Result[T, Exception]:
        self.thread.join()
        return self.queue.get()


def threaded(func: Callable[P, T]) -> Callable[P, Thread[P, T]]:
    """
    함수를 별도의 스레드에서 실행하고 스레드 객체를 반환하는 데코레이터.

    Returns:
        threading.Thread: 함수 실행을 담당하는 스레드 객체.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs):
        return Thread(func, *args, **kwargs)

    return wrapper
