import mimetypes
from pathlib import Path, PurePath

from .response import Response

GEMTEXT_EXT = ".gmi"

mimetypes.init()
mimetypes.add_type("gemini/text", GEMTEXT_EXT)


class Vhost:

    def __init__(self, rootpath, indexfile):
        self.rootpath = rootpath
        self.indexfile = indexfile

    def process(self, relpath, query, cert):
        response = Response()

        if relpath is None:
            relpath = ""

        fpath = Path(self.rootpath, relpath).resolve()

        if fpath.is_dir():
            fpath = Path(fpath, self.indexfile)
        elif not fpath.is_file():
            fpath = Path(PurePath(fpath).with_suffix(GEMTEXT_EXT))

        try:
            fpath = fpath.resolve(True)
            mimetype = mimetypes.guess_type(fpath)[0]
            response.success(mimetype, fpath.read_bytes())
        except FileNotFoundError:
            response.permfail(1, "Resource not found")

        return response
