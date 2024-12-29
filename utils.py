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
