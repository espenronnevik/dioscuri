import asyncio
import ssl


class DioscuriServer:

    def __init__(self, cert_file, key_file):
        self.ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_ctx.load_default_certs(ssl.Purpose.CLIENT_AUTH)
        self.ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        self.ssl_ctx.load_cert_chain(cert_file, key_file)

        self.loop = asyncio.get_event_loop()

    async def socket_handler(self, reader, writer):
        pass

    async def run(self):
        self.loop.run_forever()
