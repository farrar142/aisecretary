def translate(text: str, **kwargs):
    for key, value in kwargs.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def t(text: str, **kwargs):
    return translate(text, **kwargs)
