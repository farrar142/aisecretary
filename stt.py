from typing import Any, TypedDict
import numpy as np
import whisper


class STTResult(TypedDict):
    text: str


class STT:

    def __init__(self):
        pass

    def run(self, data: np.ndarray) -> STTResult: ...

    @classmethod
    def LocalSTT(cls) -> "STT":
        return LocalWhisper()


class LocalWhisper(STT):
    def __init__(self):
        self.model = self.load_whisper()

    def load_whisper(self):
        return whisper.load_model("medium", device="cuda")

    def run(self, data: np.ndarray) -> STTResult:
        return self.model.transcribe(data, fp16=False, language="ko")  # type:ignore
