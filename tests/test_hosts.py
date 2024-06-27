import shutil

import pytest

from digitalsoup.dioscuri.hosts import Vhost
from digitalsoup.dioscuri.response import StatusType

INDEX_GMI = "# INDEX.GMI TEST FILE"
ANOTHER_GMI = "# ANOTHER.GMI TEST FILE"


@pytest.fixture(scope="module")
def vhost(tmp_path_factory):
    tpath = tmp_path_factory.mktemp("content")

    indexf = tpath / "index.gmi"
    with indexf.open("w") as f:
        f.write(INDEX_GMI)

    anotherf = tpath / "another.gmi"
    with anotherf.open("w") as f:
        f.write(ANOTHER_GMI)

    vhost = Vhost(tpath, "index.gmi")
    yield vhost

    shutil.rmtree(tpath)


class TestVhost:

    def test_index_ext(self, vhost):
        resp = vhost.process("index.gmi", None, None)
        assert resp.statustype == StatusType.SUCCESS
        assert resp.statuscode == 20

    def test_index_noext(self, vhost):
        resp = vhost.process("index", None, None)
        assert resp.statustype == StatusType.SUCCESS
        assert resp.statuscode == 20

    def test_index_root(self, vhost):
        resp = vhost.process("", None, None)
        assert resp.statustype == StatusType.SUCCESS
        assert resp.statuscode == 20

    def test_another_ext(self, vhost):
        resp = vhost.process("another.gmi", None, None)
        assert resp.statustype == StatusType.SUCCESS
        assert resp.statuscode == 20

    def test_another_noext(self, vhost):
        resp = vhost.process("another", None, None)
        assert resp.statustype == StatusType.SUCCESS
        assert resp.statuscode == 20

    def test_another_not_exist(self, vhost):
        resp = vhost.process("not_exist.gmi", None, None)
        assert resp.statustype == StatusType.PERMFAIL
        assert resp.statuscode == 51
