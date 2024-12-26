from typing import Iterable
import openai
from returns.result import safe

from ai.functions import Function, FunctionResult
from decorators.throttles import execution_limit
from .context import Message, System, Assistant, ContextLoader
from ai.tasks import *


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

    def get_response(self, messages: Iterable[Message]) -> str:
        total_context: list[Message] = [
            System(content="You are a helpful assistant"),
        ]
        total_context.extend(messages)

        @execution_limit(3)
        def recursive_response(messages: Iterable[Message]) -> str:
            response = openai.chat.completions.create(
                model=self.model_name,
                messages=messages,
                function_call="auto",
                functions=list(map(lambda x: x.dict(), Function.get_functions())),
            )
            choice = response.choices[0]
            if choice.finish_reason == "function_call":
                if choice.message.function_call:
                    call = choice.message.function_call
                    result = Function.function_call(call)
                    assist_message = Assistant(function_call=call.model_dump())
                    result_message = result.map(FunctionResult.to_message).unwrap()
                    return recursive_response(
                        [*messages, assist_message, result_message]
                    )
            return (choice.message.content or "").strip()

        return recursive_response(total_context)
