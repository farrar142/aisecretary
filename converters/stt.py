from typing import Any, TypedDict
import openai
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
        self.model = self.load_whisper()

    def load_whisper(self):
        import whisper

        return whisper.load_model("medium", device="cuda:1")

    def runner(self, data: RecordedFile) -> str:
        return self.model.transcribe(
            data.translate_16_to_32(), fp16=False, language="ko"
        )[
            "text"
        ]  # type:ignore


class RemoteWhisper(STT):
    def runner(self, data: RecordedFile) -> str:
        with data.to_file() as f:
            print(f)
            try:
                return openai.audio.transcriptions.create(
                    file=f,
                    model="whisper-1",
                ).text
            except Exception as e:
                print(e)
                raise e
