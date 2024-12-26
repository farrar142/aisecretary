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


class ContextLoader:
    @attempt
    def load_context(self) -> list[Message]: ...
    @attempt
    def if_load_failed(self) -> list[Message]: ...
    def save_context(self, message: Message): ...

    def run(self, func: Callable[[list[Message]], str]):
        def inner(prompt: str) -> str:
            user_message = User(content=prompt)
            context = self.load_context().lash(self.__class__.if_load_failed)
            context.map(lambda x: x.append(user_message)).map(
                lambda x: self.save_context(user_message)
            )
            result = context.map(func)
            # AI 응답 생성

            # 응답 저장
            result.map(lambda reply: self.save_context(Assistant(content=reply)))
            return result.unwrap()

        return inner

    @classmethod
    def JsonLoader(cls):
        return JsonContextLoader("context.json")

    @classmethod
    def InmemoryLoader(cls):
        return InmemoryContextLoader(10)


class JsonContextLoader(ContextLoader):
    def __init__(self, file_name: str, limit: int = 10):
        self.file_name = file_name
        self.limit = limit

    # JSON 파일에서 컨텍스트 로드
    @attempt
    def load_context(self) -> list[Message]:
        with open(self.file_name, "r") as f:
            data = json.load(f)
            return data[-self.limit :]  # 최신 10개의 대화만 반환

    @attempt
    def if_load_failed(self) -> list[Message]:
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


class InmemoryContextLoader(ContextLoader):
    def __init__(self, max_len: int):
        self.context = deque([], maxlen=max_len)

    @attempt
    def load_context(self) -> Iterable[Message]:
        return self.context

    def save_context(self, message: Message):
        self.context.append(message)


# # 데코레이터
# def memorize_context_json(func: Callable[[Iterable[Message], str], str]):
#     loader = JsonContextLoader(file_name="context.json")

#     def wrapper(text: str, model_name: str = "gpt-3.5-turbo"):
#         # 컨텍스트 로드
#         context = loader.load_context()
#         # 사용자 입력 추가
#         context.map(lambda x: x.append(User(text)))
#         loader.save_message("user", text)
#         result = context.map(lambda context: func(context, model_name))
#         # AI 응답 생성

#         # 응답 저장
#         result.map(lambda reply: loader.save_message("assistant", reply))
#         return result

#     return wrapper


# def memorize_context(func: Callable[[Iterable[Message], str], str]):
#     context: deque[Message] = deque([], maxlen=10)

#     def inner(text: str, model_name: str = "gpt-3.5-turbo"):
#         context.append(User(content=text))
#         reply = func(context, model_name)
#         context.append(Assistant(content=reply))
#         return Result(reply)

#     return inner
