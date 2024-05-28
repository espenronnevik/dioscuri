import asyncio
import re
import ssl

from .listener import Listener

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

    def add_listener(self, hostname, port=1965):
        if port in self.listeners and hostname in self.listeners[port]:
            return

        listener = Listener(hostname, port)
        self.listeners.setdefault(port, {})
        self.listeners[port][hostname] = listener
        self.loop.run_until_complete(listener.start(self.socket_handler, self.ssl_ctx))

    async def remove_listener(self, hostname, port):
        if port not in self.listeners or hostname not in self.listeners[port]:
            return

        await self.listeners[port][hostname].stop()
        del self.listeners[port][hostname]

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
