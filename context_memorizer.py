from collections import deque
from functools import partial
import json
from typing import Callable, Iterable, Union
from openai.types.chat import (
    ChatCompletionSystemMessageParam as _System,
    ChatCompletionAssistantMessageParam as _Assistant,
    ChatCompletionUserMessageParam as _User,
)
from returns.maybe import Maybe, maybe
from returns.result import safe, attempt, Success, Result

User = partial(_User, role="user")
System = partial(_System, role="system")
Assistant = partial(_Assistant, role="assistant")
Message = Union[_User, _System, _Assistant]


class JsonContextLoader:
    def __init__(self, file_name: str, limit: int = 10):
        self.file_name = file_name
        self.limit = limit

    # JSON 파일에서 컨텍스트 로드
    @attempt
    def load_context(self) -> list[Message]:
        with open(self.file_name, "r") as f:
            data = json.load(f)
            return data[-self.limit :]  # 최신 10개의 대화만 반환

    @safe
    def create_file(self) -> list[Message]:
        with open(self.file_name, "w+", encoding="utf-8") as f:
            f.write(json.dumps([]))
        return []

    # JSON 파일에 메시지 저장
    def save_message(self, role: str, content: str):
        with open(self.file_name, "r") as f:
            data: list[dict] = json.load(f)

        data.append({"role": role, "content": content})
        with open(self.file_name, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


# 데코레이터
def memorize_context_json(func: Callable[[Iterable[Message], str], str]):
    loader = JsonContextLoader(file_name="context.json")

    def wrapper(text: str, model_name: str = "gpt-3.5-turbo"):
        # 컨텍스트 로드
        context = loader.load_context().lash(JsonContextLoader.create_file)
        # 사용자 입력 추가
        context.map(lambda x: x.append(User(text)))
        loader.save_message("user", text)
        result = context.map(lambda context: func(context, model_name))
        # AI 응답 생성

        # 응답 저장
        result.map(lambda reply: loader.save_message("assistant", reply))
        return result

    return wrapper


def memorize_context(func: Callable[[Iterable[Message], str], str]):
    context: deque[Message] = deque([], maxlen=10)

    def inner(text: str, model_name: str = "gpt-3.5-turbo"):
        context.append(User(content=text))
        reply = func(context, model_name)
        context.append(Assistant(content=reply))
        return Result(reply)

    return inner
