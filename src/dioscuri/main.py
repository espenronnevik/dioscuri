from .dioscuriserver import DioscuriServer


def main(cert_file, key_file):
    server = DioscuriServer(cert_file, key_file)
    server.add_listener("127.0.0.1")
    server.run()
