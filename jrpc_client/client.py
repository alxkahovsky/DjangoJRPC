import tempfile
from types import NoneType
from typing import Optional
from urllib.parse import urlparse
import http.client
from abc import ABC, abstractmethod
import http.client
import ssl
import json



class Transport(ABC):
    @abstractmethod
    def call(self,
        scheme: str,
        host: str,
        port: int,
        url: str,
        method: str,
        params: dict,
        call_id: int,
        version: str,
        certfile: Optional[str] = None,
        keyfile: Optional[str] = None):
        pass



class HttpTransport(Transport):
    def call(
        self,
        scheme: str,
        host: str,
        port: int,
        url: str,
        method: str,
        params: dict,
        call_id: int,
        version: str,
        certdata: Optional[str] = None,
        keydata: Optional[str] = None) -> dict:
        # ToDo [ ] вынести в отдельные методы работу с сертификатами
        if scheme == "https":
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            if certdata and keydata:
                with tempfile.NamedTemporaryFile(delete=False) as certfile, tempfile.NamedTemporaryFile(
                        delete=False) as keyfile:
                    certfile.write(certdata.encode('utf-8'))
                    certfile.flush()
                    keyfile.write(keydata.encode('utf-8'))
                    keyfile.flush()
                    context.load_cert_chain(certfile.name, keyfile.name)
                    conn = http.client.HTTPSConnection(host, port, context=context)
            else:
                conn = http.client.HTTPSConnection(host, port, context=context)
        else:
            conn = http.client.HTTPConnection(host, port)
        payload = self._create_payload(method, params, call_id, version)
        headers = self._create_headers()
        conn.request("POST", url, body=payload, headers=headers)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8")
        conn.close()
        return json.loads(data)


    @staticmethod
    def _create_payload(method, params, call_id, version) -> json:
        if not isinstance(params, (dict, list, NoneType)):
            raise ValueError(f'Params "{params}" are invalid')
        return json.dumps(
            {
                'jsonrpc': version,
                'method': method,
                'params': params or {},
                'id': call_id
            }
        )

    @staticmethod
    def _create_headers() -> dict:
        return {"Content-Type": "application/json"}


class WebSocketTransport(Transport):
    def call(self, scheme, host, port, url, method, params, call_id, version, certfile=None, keyfile=None) -> dict:
        # Пример реализации WebSocket транспорта (заглушка)
        print(f"WebSocket call to {scheme}://{host}:{port}")
        return {"jsonrpc": "2.0", "result": "pong", "id": 1}


class UrlParser:
    def __init__(self, url):
        self.url = url
        self.parsed_url = urlparse(url)

    @property
    def scheme(self) -> str:
        return self.parsed_url.scheme.lower()

    @property
    def host(self) -> str:
        return self.parsed_url.hostname

    @property
    def port(self) -> int:
        return self.parsed_url.port

    @property
    def path(self) -> str:
        return self.parsed_url.path


class VersionValidator:
    @staticmethod
    def validate(version) -> str:
        if version not in ('2.0',):
            raise ValueError(f'Version "{version}" is not supported')
        return version


class JrpcServer:
    def __init__(self, url, version, transport: Transport, certfile=None, keyfile=None):
        self.url_parser = UrlParser(url)
        self.version = VersionValidator.validate(version)
        self.transport = transport
        self.certfile = certfile
        self.keyfile = keyfile

    def call_method(self, method, params=None, call_id=1) -> dict:
        scheme = self.url_parser.scheme
        host = self.url_parser.host
        port = self.url_parser.port
        url = self.url_parser.path
        version = self.version
        return self.transport.call(scheme, host, port, url,
                                   method, params, call_id, version,
                                   self.certfile, self.keyfile)


http_transport = HttpTransport()
websocket_transport = WebSocketTransport()


__all__ = ['JrpcServer', 'http_transport', 'websocket_transport']
