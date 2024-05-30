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

    def input(self, prompt, statusdigit=0):
        self.statustype = StatusType.INPUT
        self.statuscode = 10 + statusdigit
        self.data = f"{self.statuscode} {prompt} {CRLF}".encode()

    def success(self, mimetype, content, statusdigit=0):
        self.statustype = StatusType.SUCCESS
        self.statuscode = 20 + statusdigit
        self.data = f"{self.statuscode} {mimetype} {CRLF}".encode() + content

    def redirect(self, uri, statusdigit=0):
        self.statustype = StatusType.REDIRECT
        self.statuscode = 30 + statusdigit
        self.data = f"{self.statuscode} {uri} {CRLF}".encode()

    def tempfail(self, statusdigit=0, message=None):
        self.statustype = StatusType.TEMPFAIL
        self.statuscode = 40 + statusdigit
        if message is None:
            self.data = f"{self.statuscode} {CRLF}".encode()
        else:
            self.data = f"{self.statuscode} {message} {CRLF}".encode()

    def permfail(self, statusdigit=0, message=None):
        self.statustype = StatusType.PERMFAIL
        self.statuscode = 50 + statusdigit
        if message is None:
            self.data = f"{self.statuscode} {CRLF}".encode()
        else:
            self.data = f"{self.statuscode} {message} {CRLF}".encode()

    def auth(self, statusdigit=0, message=None):
        self.statustype = StatusType.AUTH
        self.statuscode = 60 + statusdigit
        if message is None:
            self.data = f"{self.statuscode} {CRLF}".encode()
        else:
            self.data = f"{self.statuscode} {message} {CRLF}".encode()
