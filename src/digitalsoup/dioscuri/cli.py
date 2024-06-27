import pathlib
import tomllib
from argparse import ArgumentParser

from .server import Server


def parse_arguments():
    parser = ArgumentParser(
        prog="dioscuri",
        description="Serving text and files using the Gemini protocol",
    )
    parser.add_argument("--config", type=pathlib.Path, required=True)
    return parser.parse_args()


def main():
    args = vars(parse_arguments())

    configf = args["config"].resolve()
    with open(configf, "rb") as f:
        config = tomllib.load(f)

    server = Server()
    server.run(config)
