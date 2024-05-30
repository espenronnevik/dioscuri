import mimetypes
from pathlib import Path, PurePath

from .response import Response, StatusType

GEMTEXT_EXT = ".gmi"

mimetypes.init()
mimetypes.add_type("gemini/text", GEMTEXT_EXT)


class Vhost:

    def __init__(self, contentroot, index):
        self.root = contentroot
        self.index = index

    def process(self, request):
        req_pure = PurePath(request)

        if req_pure.suffix != GEMTEXT_EXT:
            req_path = Path(req_pure.parent, req_pure.stem + GEMTEXT_EXT)
        else:
            req_path = Path(req_pure)
        path = Path(self.root, req_path.resolve())

        if path.is_dir():
            path = Path(path, self.index)

        try:
            path = path.resolve(True)
            mimetype = mimetypes.guess_type(path)
            return Response().success(mimetype, path.read_bytes())
        except FileNotFoundError:
            return Response().permfail(1, "Resource not found")
