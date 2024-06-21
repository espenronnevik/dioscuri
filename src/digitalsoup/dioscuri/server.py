import asyncio
import re
import ssl
from hashlib import sha1
from urllib.parse import unquote

from .listener import Listener
from .hosts import Vhost
from .response import Response

REQUEST_PATTERN = re.compile(
    r"^(?P<scheme>\w+)://"
    r"(?P<host>[\w.]+)"
    r"(?::(?P<port>\d+))?"
    r"(?:/(?P<path>[\w.]+/?)*)?"
    r"(?:\?(?P<query>[\w ]+))?$"
)


class Server:

    def __init__(self, workers):
        self.listeners = {}
        self.domains = {}
        self.sem = asyncio.Semaphore(workers)

        self.loop = None
        self.ssl_ctx = None

    def setup_ssl(self, cert_file, key_file):
        self.ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_ctx.load_default_certs(ssl.Purpose.CLIENT_AUTH)
        self.ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        self.ssl_ctx.load_cert_chain(cert_file, key_file)

    def add_listener(self, address, port):
        if port in self.listeners and address in self.listeners[port]:
            return None

        listener = Listener(address, port)
        self.listeners.setdefault(port, {})
        self.listeners[port][address] = listener
        self.loop.run_until_complete(listener.start(self.socket_handler, self.ssl_ctx))

    async def remove_listener(self, address, port):
        if port not in self.listeners or address not in self.listeners[port]:
            return None

        await self.listeners[port][address].stop()
        del self.listeners[port][address]

    def add_vhost(self, domain, rootpath):
        if domain not in self.domains:
            self.domains[domain] = Vhost(rootpath, "index.gmi")

    def remove_host(self, host):
        if host not in self.domains:
            return None

        del self.domains[host]

    @staticmethod
    async def _write_close(stream, response):
        if response is not None:
            stream.write(response.data)
            await stream.drain()
        stream.close()

    async def validate_request(self, stream, request):
        response = Response()

        if len(request) > 1024:
            response.permfail(9, "Request exceeded limit")
            await self._write_close(stream, response)
            return None

        request = unquote(request.decode()).strip()
        m_request = REQUEST_PATTERN.match(request)

        if m_request is None:
            response.permfail(9, "Invalid request")
            await self._write_close(stream, response)
            return None

        scheme = m_request.group("scheme")
        host = m_request.group("host")
        # port = m_request.group("port")
        path = m_request.group("path")
        query = m_request.group("query")

        if scheme != "gemini" or host not in self.domains:
            response.permfail(3, "Request for resource denied")
            await self._write_close(stream, response)
            return None

        return {"host": host, "path": path, "query": query}

    async def socket_handler(self, reader, writer):

        if self.sem.locked():
            response = Response()
            response.tempfail(4)
            await self._write_close(writer, response)
            return None

        async with self.sem:
            try:
                request = await reader.readline()
            except asyncio.IncompleteReadError:
                await self._write_close(writer, None)
                return None

            url_info = await self.validate_request(writer, request)
            if url_info is None:
                return None

            peercert = writer.get_extra_info("ssl_object").getpeercert(True)
            if peercert is not None:
                peerfp = sha1(peercert).digest()

            vhost = self.domains[url_info["host"]]
            response = vhost.process(url_info["path"], url_info["query"], peerfp)
            await self._write_close(writer, response)

    def run(self):
        if self.ssl_ctx is None:
            raise RuntimeError("SSL setup is required before starting server")

        if len(self.listeners) == 0:
            raise RuntimeError("Unable to start server without configured listeners")

        if len(self.domains) == 0:
            raise RuntimeError("Unable to start server without configured hosts")

        self.loop = asyncio.get_event_loop()
        self.loop.run_forever()
