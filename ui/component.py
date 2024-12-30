import sys
from typing import Callable, Generic, ParamSpec, Self, TypeVar

from PyQt6.QtWidgets import QApplication

from translations import translate

T = TypeVar("T")
P = ParamSpec("P")


class Component:
    application: QApplication

    def __init__(self, name: str, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.initialize_app()

    @classmethod
    def initialize_app(cls) -> "QApplication":
        if not (application := getattr(cls, "__application", None)):
            application = QApplication(sys.argv)
            setattr(cls, "__application", application)
        return application

    def __call__(self, func: Callable[P, T]):

        _instance = func(*self.args, **self.kwargs)
        setattr(self.__class__, self.name, _instance)

        def inner(*args: P.args, **kwargs: P.kwargs):
            return _instance

        return inner

    @classmethod
    def inject(cls, name: str):
        def fget(self):
            if component := getattr(cls, name):
                return component
            raise Exception(
                translate("{name}은 아직 초기화 되지 않았습니다.", name=name)
            )

        return property(fget)
