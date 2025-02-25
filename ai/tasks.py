from datetime import datetime
import subprocess
from ai.functions import function_register


@function_register(
    application_name="Window Application Name (notepad.exe, calculator.exe )",
)
def open_window_application(application_name: str) -> bool:
    "Windows 어플리케이션을 실행하는 함수."
    try:
        subprocess.Popen([application_name])  # 메모장을 실행
        return True
    except Exception as e:
        return False


@function_register()
def now():
    "현재 시각을 알려줍니다"
    return str(datetime.now())
