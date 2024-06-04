import pathlib
from argparse import ArgumentParser

from dioscuriserver import DioscuriServer


def parse_arguments():
    parser = ArgumentParser(
        prog="Dioscuri Server",
        description="Serving text and files using the Gemini protocol",
    )
    parser.add_argument("--keyfile", type=pathlib.Path, required=True)
    parser.add_argument("--certfile", type=pathlib.Path, required=True)
    parser.add_argument("--rootpath", type=pathlib.Path, required=True)
    parser.add_argument("--domain", default="localhost")
    parser.add_argument("--listen", default="127.0.0.1:1965")
    return parser.parse_args()


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

    if ":" in args["listen"]:
        addr, port = args["listen"].rsplit(":")
    else:
        addr = args["listen"]
        port = "1965"

    server = DioscuriServer(certfile, keyfile)
    server.add_listener(addr, port)
    server.add_vhost(args["domain"], rootpath)
    server.run()


if __name__ == "__main__":
    main()
