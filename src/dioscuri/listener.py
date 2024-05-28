import asyncio


class Listener:

    def __init__(self, hostname, port):
        self.server = None
        self.hostname = hostname
        self.port = port

    def start(self, callback, ssl_ctx):
        if self.server is None:
            self.server = asyncio.start_server(callback, self.hostname, self.port, ssl=ssl_ctx)
        return self.server

    async def stop(self):
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()
            self.server = None
