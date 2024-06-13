import pathlib
from argparse import ArgumentParser

import ifaddr

from .server import Server


def parse_arguments():
    parser = ArgumentParser(
        prog="dioscuri",
        description="Serving text and files using the Gemini protocol",
    )
    parser.add_argument("--keyfile", type=pathlib.Path, required=True)
    parser.add_argument("--certfile", type=pathlib.Path, required=True)
    parser.add_argument("--rootpath", type=pathlib.Path, required=True)
    parser.add_argument("--domain", required=True)
    parser.add_argument("--port", default="1965")
    parser.add_argument("--address", action="append")
    return parser.parse_args()


def get_ifaddrs(addresses):
    addrs = set()
    if addresses is None:
        for adapter in ifaddr.get_adapters():
            for ip in adapter.ips:
                if ip.is_IPv6:
                    addrs.add(ip.ip[0])
                else:
                    addrs.add(ip.ip)
    else:
        addrs.update(set(addresses))
    return addrs


def main():
    args = vars(parse_arguments())

    if args["certfile"] is None or args["keyfile"] is None:
        raise ValueError("Server is unable to start without a TLS certificate")

    certfile = args["certfile"].resolve()
    keyfile = args["keyfile"].resolve()

    if args["rootpath"] is None:
        raise ValueError("Server is unable to start without a root datapath")

    rootpath = args["rootpath"].resolve()
    if not rootpath.is_dir():
        raise ValueError(f"Root datapath {rootpath} is not a directory")

    server = Server(certfile, keyfile)

    for addr in get_ifaddrs(args["listen"]):
        server.add_listener(addr, args["port"])

    server.add_vhost(args["domain"], rootpath)
    server.run()
