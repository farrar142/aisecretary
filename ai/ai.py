from typing import Iterable
import openai
from returns.result import attempt, safe, Result
from returns.maybe import Maybe

from functions import Function, FunctionResult, get_weather
from .context import Message, System, FunctionM, ContextLoader


class AI:
    def __init__(self, context_loader: ContextLoader):
        self.context_loader = context_loader

    def get_response(self, messages: Iterable[Message]) -> str: ...

    @safe
    def run(self, message: str):
        return self.context_loader.run(self.get_response)(message)

    @classmethod
    def ChatGPT(cls) -> "AI":
        return ChatGPT(ContextLoader.JsonLoader())


class ChatGPT(AI):
    model_name = "gpt-3.5-turbo"

    def recursive_response(self, messages: Iterable[Message]) -> str:
        response = openai.chat.completions.create(
            model=self.model_name,
            messages=messages,
            function_call="auto",
            functions=[get_weather.dict()],
        )
        choice = response.choices[0]
        if choice.finish_reason == "function_call":
            call = Maybe.from_optional(choice.message.function_call)
            result = call.bind(Function.function_call)
            message = result.map(FunctionResult.to_message).unwrap()
            return self.recursive_response([*messages, message])
        return (choice.message.content or "").strip()

    def get_response(self, messages: Iterable[Message]) -> str:
        total_context: list[Message] = [
            System(content="You are a helpful assistant"),
        ]
        total_context.extend(messages)
        return self.recursive_response(total_context)
