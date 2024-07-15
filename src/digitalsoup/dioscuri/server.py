import asyncio
import re
import ssl
from hashlib import sha1
from pathlib import Path
from urllib.parse import unquote

import ifaddr

from .hosts import Vhost
from .listener import Listener
from .response import Response

REQUEST_PATTERN = re.compile(
    r"^(?P<scheme>\w+)://"
    r"(?P<host>[\w.]+)"
    r"(?::(?P<port>\d+))?"
    r"(?:/(?P<path>[\w.]+/?)*)?"
    r"(?:\?(?P<query>[\w ]+))?$"
)


def ifaddrs(ipv4=True, ipv6=True):
    addrs = set()
    for adapter in ifaddr.get_adapters():
        for ip in adapter.ips:
            if ip.is_IPv6 and ipv6:
                addrs.add(ip.ip[0])
            if ip.is_IPv4 and ipv4:
                addrs.add(ip.ip)
    return list(addrs)


class Server:

    def __init__(self):
        self.config = None
        self.sem = None
        self.ssl_ctx = None

        self.listeners = {}
        self.domains = {}
        self.loop = asyncio.get_event_loop()

    def setup_ssl(self, cert, key):
        self.ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_ctx.load_default_certs(ssl.Purpose.CLIENT_AUTH)
        self.ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        self.ssl_ctx.load_cert_chain(cert, key)

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

            print(f"Request: {url_info}")

            peerfp = None
            peercert = writer.get_extra_info("ssl_object").getpeercert(True)
            if peercert is not None:
                peerfp = sha1(peercert).digest()

            vhost = self.domains[url_info["host"]]
            response = vhost.process(url_info["path"], url_info["query"], peerfp)

            print(f"Returning {response}")
            await self._write_close(writer, response)

    def run(self, config):
        config_cert = config.get("tlscert")
        config_key = config.get("tlskey")
        if config_cert is None or config_key is None:
            raise ValueError("Config error: Server is unable to start without configured TLS")

        certfile = Path(config_cert).resolve()
        keyfile = Path(config_key).resolve()
        if not (certfile.is_file() or keyfile.is_file()):
            raise ValueError("Config error: tlscert and tlskey must be path to a file")

        self.setup_ssl(certfile, keyfile)

        config_listeners = config.get("listeners", [])
        if len(config_listeners) == 0:
            raise ValueError("Config error: Unable to start server without any configured listeners")

        for item in config_listeners:
            port = item["port"]
            addrlist = item["address"]
            if "all" in addrlist:
                addrlist = ifaddrs()
            for addr in addrlist:
                self.add_listener(addr, port)

        sites = config.get("site", {})
        if len(sites) == 0:
            raise ValueError("Config error: Unable to start server without any configured sites")

        for domain, props in sites.items():
            enabled = props.get("enabled", False)
            rootpath = props.get("root", None)
            if enabled and rootpath is not None:
                self.add_vhost(domain, Path(rootpath))

        self.sem = asyncio.Semaphore(config.get("workers", 100))

        self.loop.run_forever()
