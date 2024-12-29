from typing import Any, TypedDict
from recorder.recorded_file import RecordedFile


class STTResult(TypedDict):
    text: str


class STT:

    def __init__(self):
        pass

    def runner(self, data: RecordedFile) -> str: ...

    def run(self, data: RecordedFile) -> str:
        return self.runner(data)

    @classmethod
    def LocalSTT(cls) -> "STT":
        return LocalWhisper()

    @classmethod
    def RemoteSTT(cls) -> "STT":
        return RemoteWhisper()


class LocalWhisper(STT):
    def __init__(self):
        from client_loaders import whisper_loader

        self.client = whisper_loader()

    def runner(self, data: RecordedFile) -> str:
        return self.client.transcribe(
            data.translate_16_to_32(), fp16=False, language="ko"
        )[
            "text"
        ]  # type:ignore


class RemoteWhisper(STT):
    def __init__(self):
        from client_loaders import openai_loader

        self.client = openai_loader()

    def runner(self, data: RecordedFile) -> str:
        with data.to_file() as f:
            try:
                return self.client.audio.transcriptions.create(
                    file=f,
                    model="whisper-1",
                ).text
            except Exception as e:
                print(e)
                raise e
