from pathlib import Path

GEMTEXT_EXT = ".gmi"

class Vhost:

    def __init__(self, contentroot, index):
        self.root = contentroot
        self.index = index

    def process(self, request):
        result = {}
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
            result["type"] = "success"
            result["status"] = 20
            result["data"] = path
        except FileNotFoundError:
            result["type"] = "error"
            result["status"] = 51
            result["data"] = "Resource not found"

        return result
