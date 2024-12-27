from typing import Iterable
import openai
from openai.types.chat.chat_completion import Choice
from returns.result import safe
from returns.maybe import maybe

from ai.functions import Function, FunctionResult
from exceptions import RequestLimitError
from ai.context import Message, System, Assistant, ContextLoader
from ai.tasks import *
from settings import Setting


class AI:
    def __init__(self, context_loader: ContextLoader):
        self.context_loader = context_loader

    def runner(self, messages: Iterable[Message]) -> str: ...

    @safe
    def run(self, message: str):
        executor = self.context_loader.run(self.runner)
        return executor(message)

    @classmethod
    def ChatGPT(cls) -> "AI":
        return ChatGPT(ContextLoader.JsonLoader())


# 챗지피티 리커시브 리스폰스 클래스를 만들어서 runner분리
class ChatGPTResponseSession:
    model_name = Setting.CHAT_GPT_MODEL_NAME

    def __init__(self, request_limit: int = 3):
        self.request_limit = request_limit
        self.request_count = 0

    @maybe
    def function_call(self, choice: Choice, messages: Iterable[Message]):
        if choice.finish_reason != "function_call":
            return
        if choice.message.function_call == None:
            return
        call = choice.message.function_call
        result = Function.function_call(call)
        assist_message = Assistant(function_call=call.model_dump())
        result_message = result.map(FunctionResult.to_message).unwrap()
        return self.recursive_response([*messages, assist_message, result_message])

    def recursive_response(self, messages: Iterable[Message]) -> str:
        if self.request_limit < self.request_count:
            raise RequestLimitError
        response = openai.chat.completions.create(
            model=self.model_name,
            messages=messages,
            function_call="auto",
            functions=list(map(lambda x: x.dict(), Function.get_functions())),
        )
        choice = response.choices[0]
        content = (choice.message.content or "").strip()
        self.request_count += 1
        return self.function_call(choice, messages).value_or(content)

    def run(self, messages: Iterable[Message]) -> str:
        total_context: list[Message] = [
            System(content="You are a helpful assistant"),
        ]
        total_context.extend(messages)
        return self.recursive_response(total_context)


class ChatGPT(AI):
    def runner(self, messages: Iterable[Message]) -> str:
        return ChatGPTResponseSession(Setting.CHAT_LIMIT_PER_SESSION).run(messages)
