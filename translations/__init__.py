def translate(text: str, **kwargs):
    for key, value in kwargs:
        text.replace("{{text}}", value)
    return text


t = translate
