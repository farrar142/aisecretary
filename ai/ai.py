from typing import Iterable
import openai
from returns.result import attempt, safe, Result
from .context import Message, System, ContextLoader


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
        response = openai.chat.completions.create(
            model=self.model_name,
            messages=total_context,
        )
        return (response.choices[0].message.content or "").strip()
