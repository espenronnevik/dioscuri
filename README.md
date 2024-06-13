# Dioscuri - a Gemini capsule server

## Description
This software is written in Python3 and is a server speaking the 
[Gemini protocol](https://geminiprotocol.net/docs/protocol-specification.gmi)
and serves up [Gemtext](https://geminiprotocol.net/docs/gemtext-specification.gmi) 
files and other arbitrary filetypes by mimetype. 

It is named after the greek Gemini twins Castor and Pollux, known together as the Dioscuri. Dioscuri serves as my 
first personal project at [boot.dev](https://www.boot.dev) where an excersize in parsing and structuring Markdown
text reminded me of the protocol's existence. My main goals was to get experience building a Python server
using asyncio, and modern methods of packaging the sources.

The Gemini protocol is a modernized and improved version of the Gopher protocol, and focuses on being a simple way
to request and receive data, with TLS encryption being mandatory.

## Usage

```
usage: dioscuri [-h] --keyfile KEYFILE --certfile CERTFILE --rootpath ROOTPATH --domain DOMAIN [--port PORT] [--address ADDRESS]
```

The following arguments are accepted by the software with their meaning:
* --certfile - Path to your certificate in PEM-format 
* --keyfile - Path to the certificates private key in PEM-format
* --domain - The domain where you are accepting requests 
* --rootpath - The root directory of the site

The following arguments are optional:
* --port - Listen to another port than the default 1965
* --address - Specify IP addresses to accept requests from. Both IPv4 and IPv6 are allowed and multiple address 
arguments can be used

If not addresses are specified, the default is to listen to every available IP on the system.
 
### TLS:

Since TLS is required, you need a certificate and private key before you can start the server. The protocol
advises TOFU (Trust On First Use) style handling of encryption certificates, where you check and mark a certificate
as trusted the first time you encounter it, to allow the use of self-signed certificates. This is similar to how 
OpenSSH handles keys.

To generate a self-signed certificate, use one of these commands:
```
# Generate ECDSA P-256 certificate with 3650 (10 years) validity
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -days 3650 -keyout key.pem -out cert.pem

# Generate RSA 4096 certificate with 3650 (10 years) validity
openssl req -x509 -newkey rsa:4096 -nodes -days 3650 -keyout key.pem -out cert.pem
```

## Install and run

This project uses [Poetry](https://python-poetry.org) for package building and management,
and until it is published on PyPi you can use Poetry to install and run it.

```
poetry install
```

This will install Dioscuri in a virtual environment, and then you can either execute the dioscuri script in the 
environments /bin-folder, or you can use

```
poetry run dioscuri
```
