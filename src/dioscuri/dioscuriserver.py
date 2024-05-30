import asyncio
import re
import ssl

from .listener import Listener
from .vhosts import Vhost

REQUEST = re.compile(r"^(?P<protocol>\w+)://(?P<hostname>\w+\.\w+)(?P<path>/(?:\w+/?)*)?(?:\?(?P<param>\w+))?$")


class DioscuriServer:

    def __init__(self, cert_file, key_file):
        self.loop = asyncio.get_event_loop()
        self.listeners = {}
        self.vhosts = {}
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
        if host in self.vhosts:
            return

        self.vhosts[host] = Vhost(contentroot, "index.gmi")

        if default:
            self.vhosts["default"] = self.vhosts[host]

    def remove_vhost(self, host):
        if host not in self.vhosts:
            return

        del self.vhosts[host]

    async def socket_handler(self, reader, writer):
        try:
            cmd = await reader.readline()
        except asyncio.IncompleteReadError:
            return

        res = REQUEST.match(cmd)

    def run(self):
        if len(self.listeners) == 0:
            raise RuntimeError("Unable to start server without listeners")

        if len(self.vhosts) == 0:
            raise RuntimeError("Unable to start server without vhosts")

        self.loop.run_forever()
