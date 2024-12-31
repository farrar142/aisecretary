import json
from typing import Any, Callable, Iterable, Literal, Optional, Union, get_type_hints
from dotenv import load_dotenv
import os
import chardet


def detect_file_encoding(file_path: str, buffer_size: int = 1024) -> str:
    """
    파일의 인코딩 타입을 탐지하는 함수.

    Args:
        file_path (str): 인코딩을 확인할 파일 경로.
        buffer_size (int): 읽어들일 데이터의 크기. 기본값은 1024바이트.

    Returns:
        str: 탐지된 인코딩 타입. 탐지에 실패하면 'unknown' 반환.
    """
    try:
        with open(file_path, "rb") as file:
            raw_data = file.read(buffer_size)
            result = chardet.detect(raw_data)
            encoding = result.get("encoding")
            if encoding is not None:
                return encoding
            return "unknown"
    except Exception as e:
        raise RuntimeError(f"Error detecting encoding for file '{file_path}': {e}")


class SettingLoader:

    @classmethod
    def env_loader(cls):
        envs = dict[str, Any]()
        for field_name, field_type in get_type_hints(cls).items():
            # 기본값 처리
            default_value = getattr(cls, field_name, None)
            # 환경 변수에서 값 가져오기
            env_value = os.getenv(field_name)
            envs[field_name] = env_value or default_value

        return envs

    @classmethod
    def json_loader(cls, file_name="settings.json") -> dict[str, Any]:
        with open(file_name, "r", encoding=detect_file_encoding(file_name)) as f:
            return json.loads(f.read())

    @classmethod
    def json_writer(cls, data: dict[str, Any], file_name="settings.json"):
        with open(file_name, "w", encoding=detect_file_encoding(file_name)) as f:
            return json.dump(data, f, indent=2, ensure_ascii=False)


class SettingBase:

    @classmethod
    def load(cls, loader: Callable[[], dict[str, Any]]):
        env = loader()
        type_hints = get_type_hints(cls)
        values = dict()
        for field_name, field_type in type_hints.items():
            # 기본값 처리
            default_value = getattr(cls, field_name, None)

            # 주입된 환경 변수에서 값 가져오기
            env_value = env.get(field_name)

            # 환경 변수 값 우선 적용, 없으면 기본값 사용
            if env_value is not None:
                try:
                    converted_value = cls._convert_value(env_value, field_type)
                except ValueError as e:
                    raise ValueError(
                        f"Failed to convert environment variable '{field_name}' to {field_type}: {e}"
                    )
            else:
                converted_value = default_value

            # Optional 타입일 경우 None 허용
            if converted_value is None and not cls._is_optional(field_type):
                raise ValueError(
                    f"Environment variable '{field_name}' is required but not set."
                )

            setattr(cls, field_name, converted_value)

    @classmethod
    def save(
        cls,
        loader: Callable[[], dict[str, Any]],
        writer: Callable[[dict[str, Any]], None],
    ):
        cls.load(loader)
        writer(loader())

        pass

    @classmethod
    def _convert_value(cls, value: str, to_type: Any) -> Any:
        """환경 변수 값을 지정된 타입으로 변환"""
        origin_type = getattr(to_type, "__origin__", None)

        # Optional 처리
        if origin_type is Union and type(None) in to_type.__args__:
            non_optional_type = next(
                arg for arg in to_type.__args__ if arg is not type(None)
            )
            return cls._convert_value(value, non_optional_type)

        # list 처리
        if origin_type is list:
            item_type = to_type.__args__[0]
            if isinstance(value, list):
                return [cls._convert_value(v.strip(), item_type) for v in value]
            return [cls._convert_value(v.strip(), item_type) for v in value.split(",")]

        # Literal 처리
        if origin_type is Literal:
            item_type = to_type.__args__[0].__class__
            return cls._convert_value(value, item_type)

        # 기본 타입 변환
        if to_type == int:
            return int(value)
        elif to_type == float:
            return float(value)
        elif to_type == bool:
            return value.lower() in ("true", "1", "yes")
        elif to_type == str:
            return value
        else:
            raise ValueError(f"Unsupported type: {to_type}")

    @staticmethod
    def _is_optional(to_type: Any) -> bool:
        """타입이 Optional인지 확인"""
        origin_type = getattr(to_type, "__origin__", None)
        return origin_type is Union and type(None) in to_type.__args__

    @classmethod
    def to_dict(cls) -> dict[str, Any]:
        """설정된 값을 딕셔너리 형식으로 반환"""
        type_hints = get_type_hints(cls)
        result = {}
        for field_name in type_hints.keys():
            result[field_name] = getattr(cls, field_name, None)
        return result


class Setting(SettingBase, SettingLoader):
    """필드의 값을 선언하면, loader에서 env값을 읽어와 자동으로 타입에 맞게 값을 넣어주는 클래스"""

    OPEN_AI_KEY: str
    SECRETARY_NAMES: list[str]
    DISCORD_WEBHOOK_URL: str
    RECORD_DEVICE: int
    CHAT_LIMIT_PER_SESSION: int = 3
    CHAT_GPT_MODEL_NAME: str = "gpt-3.5-turbo"
    WHISPER_MODEL_NAME: str = "medium"
    WHISPER_DEVICE: Optional[str] = None
    STT: Literal["local", "remote"] = "local"
    TTS: Literal["xtts", "gtts"] = "xtts"


load_dotenv()


Setting.load(loader=Setting.json_loader)
