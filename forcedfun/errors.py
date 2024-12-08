class Http302(Exception):
    url: str

    def __init__(self, url: str) -> None:
        self.url = url
