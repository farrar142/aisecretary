from datetime import datetime
from typing import Iterable
import openai
from returns.result import attempt, safe, Result
from returns.maybe import Maybe

from ai.functions import Function, FunctionResult, get_weather
from decorators.throttles import execution_limit
from .context import Message, System, Assistant, ContextLoader


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


@Function.register(
    location="불을 키고 끌 장소 (주방, 거실 등등)",
    state="목표로 하는 상태, (True=on, False=off)",
)
def turn_light(location: str, state: bool):
    "location위치의 불을 키고 끕니다"
    return True


@Function.register()
def now():
    "현재 시각을 알려줍니다"
    return str(datetime.now())


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
                functions=[get_weather.dict(), turn_light.dict(), now.dict()],
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
