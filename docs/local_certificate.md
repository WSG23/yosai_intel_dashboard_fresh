# Local TLS Certificate

Some developers may want HTTPS even during local development. You can generate a self-signed certificate using OpenSSL:

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -sha256 -days 365 -nodes \
    -keyout certs/localhost.key -out certs/localhost.pem \
    -subj "/CN=localhost"
```

The command creates `certs/localhost.key` and `certs/localhost.pem`. Configure your reverse proxy or WSGI server to use these files.

Alternatively install [mkcert](https://github.com/FiloSottile/mkcert) and run:

```bash
mkcert -install
mkcert -key-file certs/localhost.key -cert-file certs/localhost.pem localhost
```

Keep certificate files outside version control (they are ignored by `.gitignore`).
