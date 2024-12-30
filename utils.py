from functools import reduce
from typing import Callable, Generic, Iterable, TypeVar
import pyaudio
import requests
from returns.result import safe
from returns.maybe import Maybe

from converters.stt import STTResult
from decorators.threaded import threaded
from settings import Setting


def list_audio_devices(p: pyaudio.PyAudio):
    print("사용 가능한 오디오 디바이스 목록:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"{i}: {info['name']}")


@safe
def get_record_device(p: pyaudio.PyAudio):
    def select_device():
        list_audio_devices(p)
        selected = input("디바이스 선택: ")
        return int(selected)

    return (
        Maybe.from_optional(Setting.RECORD_DEVICE).map(int).or_else_call(select_device)
    )


def get_text(data: STTResult):
    return str(data["text"]).strip()


# 텍스트 필터링
@safe(exceptions=(Exception,))
def is_ai_call(prompt: str):
    target = next(filter(lambda x: prompt.startswith(x), Setting.SECRETARY_NAMES), None)
    if target:
        return prompt.removeprefix(target)
    raise Exception


def discord_webhook(text: str):
    @threaded
    def inner(content: str):
        if not Setting.DISCORD_WEBHOOK_URL:
            return content
        requests.post(
            Setting.DISCORD_WEBHOOK_URL,
            json=dict(content=text + "\n" + content),
            headers={"Content-Type": "application/json"},
        )
        return content

    return inner


@threaded
def play_error_sound(p: pyaudio.PyAudio):
    stream = p.open(format=pyaudio.paFloat32, channels=2, rate=44100, output=True)
    with open("failed.wav", "rb") as file:
        data = file.read()
        stream.write(data)
    stream.start_stream()
    stream.close()


T = TypeVar("T")
U = TypeVar("U")


class Stream(Generic[T]):
    def __init__(self, value: Iterable[T]):
        self.value = value

    def map(self, function: Callable[[T], U]):
        value = map(function, self.value)
        return Stream(value)

    def filter(self, function: Callable[[T], bool]):
        value = filter(function, self.value)
        return Stream(value)

    def reduce(self, function: Callable[[U, T], U], default_value: U):
        value = reduce(function, self.value, default_value)
        return value

    def to_list(self):
        return list(self.value)
