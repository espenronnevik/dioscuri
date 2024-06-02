import asyncio
import re
import ssl
from hashlib import sha1
from urllib.parse import unquote

from .listener import Listener
from .hosts import Vhost
from .response import Response

REQUEST = re.compile(
    r"(?P<scheme>\w+)://(?P<authority>\w+\.\w+)(?P<path>/(?:[\w.]+/?)*)?(?:\?(?P<query>[\w ]+))?$"
)


class DioscuriServer:

    def __init__(self, cert_file, key_file):
        self.loop = asyncio.get_event_loop()
        self.listeners = {}
        self.authorities = {}
        self.ssl_ctx = None

        self.setup_ssl(cert_file, key_file)

    def setup_ssl(self, cert_file, key_file):
        self.ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_ctx.load_default_certs(ssl.Purpose.CLIENT_AUTH)
        self.ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        self.ssl_ctx.load_cert_chain(cert_file, key_file)

    def add_listener(self, address, port=1965):
        if port in self.listeners and address in self.listeners[port]:
            return

        listener = Listener(address, port)
        self.listeners.setdefault(port, {})
        self.listeners[port][address] = listener
        self.loop.run_until_complete(listener.start(self.socket_handler, self.ssl_ctx))

    async def remove_listener(self, address, port):
        if port not in self.listeners or address not in self.listeners[port]:
            return

        await self.listeners[port][address].stop()
        del self.listeners[port][address]

    def add_vhost(self, host, contentroot, default=False):
        if host in self.authorities:
            return

        self.authorities[host] = Vhost(contentroot, "index.gmi")

        if default:
            self.authorities["default"] = self.authorities[host]

    def remove_host(self, host):
        if host not in self.authorities:
            return

        del self.authorities[host]

    async def _write_close(self, stream, data):
        if data is not None:
            stream.write(data)
            await stream.drain()
        stream.close()
        await stream.wait_closed()

    async def socket_handler(self, reader, writer):
        try:
            request = await reader.readline()
        except asyncio.IncompleteReadError:
            await self._write_close(writer, None)
            return

        if len(request) > 1024:
            response = Response().permfail(9, "Request exceeded limit")
            await self._write_close(writer, response)
            return

        request_match = REQUEST.match(unquote(request.decode()))

        if request_match is None:
            response = Response().permfail(9, "Invalid request")
            await self._write_close(writer, response)
            return

        scheme = request_match.group("sceme")
        authority = request_match.group("authority")
        path = request_match.group("path")
        query = request_match.group("query")

        if scheme != "gemini" or authority not in self.authorities:
            response = Response().permfail(3, "Request for resource refused")
            await self._write_close(writer, response)
            return

        if path is None:
            path = "/"

        cert = writer.get_extra_info("ssl_object").getpeercert(True)
        if cert is not None:
            cert = sha1(cert).digest()

        response = self.authorities[authority].process(path, query, cert)
        await self._write_close(writer, response)

    def run(self):
        if len(self.listeners) == 0:
            raise RuntimeError("Unable to start server without listeners")

        if len(self.authorities) == 0:
            raise RuntimeError("Unable to start server without authorities")

        self.loop.run_forever()
