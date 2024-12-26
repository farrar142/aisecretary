import inspect
import json
from returns.maybe import Maybe, maybe
from typing import Callable, Generic, ParamSpec, TypeVar
from openai.types.chat.completion_create_params import Function as FunctionDict
from openai.types.chat.chat_completion_message import FunctionCall
from openai.types.chat import ChatCompletionFunctionMessageParam as FunctionM

T = TypeVar("T")
P = ParamSpec("P")


def generate_parameters_from_function(func: Callable[P, T], **descriptions: str):
    """
    함수의 매개변수를 기반으로 OpenAI functions의 parameters를 자동 생성합니다.
    """
    signature = inspect.signature(func)
    properties = {}
    required = []

    for name, param in signature.parameters.items():
        param_type = param.annotation
        param_default = param.default

        # 기본 데이터 타입 처리
        if param_type == str:
            param_schema = {"type": "string"}
        elif param_type == int:
            param_schema = {"type": "integer"}
        elif param_type == float:
            param_schema = {"type": "number"}
        elif param_type == bool:
            param_schema = {"type": "boolean"}
        else:
            param_schema = {"type": "string"}  # 기본값: 문자열로 처리

        # 매개변수 기본값이 없으면 필수(required)에 추가
        if param_default == inspect.Parameter.empty:
            required.append(name)
        if description := descriptions.get(name, None):
            param_schema.update(description=description)
        # 속성 추가
        properties[name] = param_schema

    # JSON Schema 반환
    return {"type": "object", "properties": properties, "required": required}


class Function(Generic[P, T]):
    functions: "dict[str, Function]" = dict()

    def __init__(self, function: Callable[P, T], **descriptions: str):
        self.name = function.__name__
        self.function = function
        self.parameters = generate_parameters_from_function(function, **descriptions)
        self.functions[self.name] = self

    def __call__(self, *args: P.args, **kwargs: P.kwargs):
        return self.function(*args, **kwargs)

    def __str__(self) -> str:
        return f"<Function: {self.name}>"

    def __repr__(self) -> str:
        return self.__str__()

    @classmethod
    def register(cls, **descriptions: str):
        def function_wrapper(function: Callable[P, T]):
            return cls(function, **descriptions)

        return function_wrapper

    @classmethod
    def function_call(cls, call: FunctionCall):
        name = call.name

        print(f"function {name} called")
        args: dict = json.loads(call.arguments)
        function = Maybe.from_optional(cls.functions.get(name, None))
        return function.map(lambda x: FunctionResult(x, x(**args)))

    def dict(self):
        return FunctionDict(
            name=self.function.__name__,
            description=self.function.__doc__ or "",
            parameters=self.parameters,
        )


class FunctionResult(Generic[P, T]):
    def __init__(self, function: Function[P, T], result: T):
        self.function = function
        self.result = result

    def to_message(self):
        return FunctionM(
            role="function", name=self.function.name, content=str(self.result)
        )


# 테스트용 함수
@Function.register(location="위치 이름", unit="단위 (metric 또는 imperial)")
def get_weather(location: str, unit: str = "metric"):
    "특정 위치의 날씨를 가져옵니다."
    print("날씨찾기!!!")
    return "맑거나 흐림"
