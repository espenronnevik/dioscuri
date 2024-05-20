from dioscuriserver import DioscuriServer


def main():
    server = DioscuriServer("cert.pem", "key.pem")
    server.run()
