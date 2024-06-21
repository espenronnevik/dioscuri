from enum import Enum

CRLF = "\r\n"


class StatusType(Enum):
    INPUT = 1
    SUCCESS = 2
    REDIRECT = 3
    TEMPFAIL = 4
    PERMFAIL = 5
    AUTH = 6


class Response:

    def __init__(self):
        self.statustype = None
        self.statuscode = None
        self.data = None

    def _reply(self, info, data=None):
        if data is not None:
            return f"{self.statuscode} {info} {CRLF}".encode() + data
        elif info is None:
            return f"{self.statuscode} {CRLF}".encode()
        else:
            return f"{self.statuscode} {info} {CRLF}".encode()

    def input(self, prompt, statusdigit=0):
        self.statustype = StatusType.INPUT
        self.statuscode = 10 + statusdigit
        self.data = self._reply(prompt)

    def success(self, mimetype, body, statusdigit=0):
        self.statustype = StatusType.SUCCESS
        self.statuscode = 20 + statusdigit
        self.data = self._reply(mimetype, body)

    def redirect(self, uri, statusdigit=0):
        self.statustype = StatusType.REDIRECT
        self.statuscode = 30 + statusdigit
        self.data = self._reply(uri)

    def tempfail(self, statusdigit=0, message=None):
        self.statustype = StatusType.TEMPFAIL
        self.statuscode = 40 + statusdigit
        self.data = self._reply(message)

    def permfail(self, statusdigit=0, message=None):
        self.statustype = StatusType.PERMFAIL
        self.statuscode = 50 + statusdigit
        self.data = self._reply(message)

    def auth(self, statusdigit=0, message=None):
        self.statustype = StatusType.AUTH
        self.statuscode = 60 + statusdigit
        self.data = self._reply(message)
