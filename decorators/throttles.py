import time
from functools import wraps
from collections import deque
from typing import Callable, Generic, ParamSpec, TypeVar

P = ParamSpec("P")
T = TypeVar("T")


class RateLimitExceededError(Exception):
    """Raised when a function exceeds the allowed rate limit."""

    pass


def rate_limit(max_calls_per_second: int):
    """
    초당 최대 호출 횟수를 제한하는 데코레이터.

    Args:
        max_calls_per_second (int): 초당 허용되는 최대 호출 횟수.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        calls = deque()  # 호출 시간 기록용

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            current_time = time.time()

            # 오래된 호출 기록 제거
            while calls and current_time - calls[0] > 1:
                calls.popleft()

            if len(calls) >= max_calls_per_second:
                raise RateLimitExceededError(
                    f"Rate limit exceeded: {max_calls_per_second} calls per second allowed."
                )

            # 현재 호출 시간 기록
            calls.append(current_time)

            # 원래 함수 실행
            return func(*args, **kwargs)

        return wrapper

    return decorator


class ExecutionLimitExceededError(Exception):
    """Raised when a function exceeds the allowed execution limit."""

    pass


P2 = ParamSpec("P2")
T2 = TypeVar("T2")


class ExecutionLimiter(Generic[P, T]):
    def __init__(self, function: Callable[P, T], max_calls: int = 1):
        self.function = function
        self.max_calls = max_calls
        self.call_count = 0

    def check_limit_exceed(self):
        if self.call_count >= self.max_calls:
            raise ExecutionLimitExceededError(
                f"Execution limit exceeded: {self.max_calls} calls allowed."
            )

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        self.check_limit_exceed()
        result = self.function(*args, **kwargs)
        self.call_count += 1  # 호출 횟수 증가
        return result


class ExecutionLimit:
    def __init__(self, max_calls: int = 1) -> None:
        self.max_calls = max_calls

    def __call__(self, function: Callable[P, T]) -> ExecutionLimiter[P, T]:
        return ExecutionLimiter(function, self.max_calls)


def execution_limit(max_calls: int):
    """
    함수 실행 횟수를 제한하는 데코레이터.

    Args:
        max_calls (int): 함수가 호출될 수 있는 최대 횟수.
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        call_count = 0  # 함수 호출 횟수 저장

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            nonlocal call_count  # 함수 호출 횟수를 변경하기 위해 nonlocal 사용
            if call_count >= max_calls:
                raise ExecutionLimitExceededError(
                    f"Execution limit exceeded: {max_calls} calls allowed."
                )

            call_count += 1  # 호출 횟수 증가
            return func(*args, **kwargs)

        return wrapper

    return decorator
