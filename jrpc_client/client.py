import http.client
import json
import ssl
import tempfile
from abc import ABC, abstractmethod
from types import NoneType
from typing import Optional, Dict, Any, Union, List
from urllib.parse import urlparse


class Transport(ABC):
    """
    Абстрактный базовый класс для транспорта, который используется для выполнения вызовов JSON-RPC.
    """

    @abstractmethod
    def call(self,
             scheme: str,
             host: str,
             port: int,
             url: str,
             method: str,
             params: Optional[Union[Dict[str, Any], List[Any]]],
             call_id: int,
             version: str,
             certfile: Optional[str] = None,
             keyfile: Optional[str] = None) -> Dict[str, Any]:
        """
        Абстрактный метод для выполнения вызова JSON-RPC.

        :param scheme: Протокол (http или https).
        :param host: Хост сервера.
        :param port: Порт сервера.
        :param url: URL-путь для вызова.
        :param method: Имя метода JSON-RPC.
        :param params: Параметры метода JSON-RPC (словарь или список).
        :param call_id: Идентификатор вызова.
        :param version: Версия JSON-RPC.
        :param certfile: Путь к файлу сертификата (опционально).
        :param keyfile: Путь к файлу ключа (опционально).
        :return: Ответ от сервера в виде словаря.
        """
        pass


class HttpTransport(Transport):
    """
    Реализация транспорта для выполнения JSON-RPC вызовов через HTTP/HTTPS.
    """

    def call(
            self,
            scheme: str,
            host: str,
            port: int,
            url: str,
            method: str,
            params: Optional[Union[Dict[str, Any], List[Any]]],
            call_id: int,
            version: str,
            certdata: Optional[str] = None,
            keydata: Optional[str] = None) -> Dict[str, Any]:
        """
        Выполняет JSON-RPC вызов через HTTP/HTTPS.

        :param scheme: Протокол (http или https).
        :param host: Хост сервера.
        :param port: Порт сервера.
        :param url: URL-путь для вызова.
        :param method: Имя метода JSON-RPC.
        :param params: Параметры метода JSON-RPC (словарь или список).
        :param call_id: Идентификатор вызова.
        :param version: Версия JSON-RPC.
        :param certdata: Данные сертификата в виде строки (опционально).
        :param keydata: Данные ключа в виде строки (опционально).
        :return: Ответ от сервера в виде словаря.
        :raises ValueError: Если схема не поддерживается.
        """
        self._validate_scheme(scheme)
        conn = self._create_connection(scheme, host, port, certdata, keydata)
        payload = self._create_payload(method, params, call_id, version)
        headers = self._create_headers()
        conn.request("POST", url, body=payload, headers=headers)
        resp = conn.getresponse()
        data = resp.read().decode("utf-8")
        conn.close()
        return json.loads(data)

    @staticmethod
    def _validate_scheme(scheme: str) -> None:
        """
        Проверяет, поддерживается ли схема (http или https).

        :param scheme: Протокол (http или https).
        :raises ValueError: Если схема не поддерживается.
        """
        if scheme not in ("http", "https"):
            raise ValueError(f'Scheme "{scheme}" is not supported. Use "http" or "https".')

    def _create_connection(
            self,
            scheme: str,
            host: str,
            port: int,
            certdata: Optional[str] = None,
            keydata: Optional[str] = None) -> Union[http.client.HTTPConnection, http.client.HTTPSConnection]:
        """
        Создает соединение с сервером.

        :param scheme: Протокол (http или https).
        :param host: Хост сервера.
        :param port: Порт сервера.
        :param certdata: Данные сертификата в виде строки (опционально).
        :param keydata: Данные ключа в виде строки (опционально).
        :return: Объект соединения (HTTPConnection или HTTPSConnection).
        """
        if scheme == "https":
            context = self._create_ssl_context(certdata, keydata)
            return http.client.HTTPSConnection(host, port, context=context)
        return http.client.HTTPConnection(host, port)

    def _create_ssl_context(self, certdata: Optional[str], keydata: Optional[str]) -> ssl.SSLContext:
        """
        Создает SSL-контекст и загружает сертификат и ключ, если они предоставлены.

        :param certdata: Данные сертификата в виде строки (опционально).
        :param keydata: Данные ключа в виде строки (опционально).
        :return: SSL-контекст.
        """
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        if certdata and keydata:
            certfile, keyfile = self._create_temp_cert_key_files(certdata, keydata)
            context.load_cert_chain(certfile.name, keyfile.name)
        return context

    @staticmethod
    def _create_temp_cert_key_files(certdata: str, keydata: str) -> tuple[tempfile.NamedTemporaryFile, tempfile.NamedTemporaryFile]:
        """
        Создает временные файлы для сертификата и ключа.

        :param certdata: Данные сертификата в виде строки.
        :param keydata: Данные ключа в виде строки.
        :return: Кортеж из временных файлов (сертификат, ключ).
        """
        certfile = tempfile.NamedTemporaryFile(delete=False)
        keyfile = tempfile.NamedTemporaryFile(delete=False)
        certfile.write(certdata.encode('utf-8'))
        certfile.flush()
        keyfile.write(keydata.encode('utf-8'))
        keyfile.flush()
        return certfile, keyfile

    @staticmethod
    def _create_payload(method: str, params: Optional[Union[Dict[str, Any], List[Any]]], call_id: int, version: str) -> str:
        """
        Создает JSON-строку для тела запроса.

        :param method: Имя метода JSON-RPC.
        :param params: Параметры метода JSON-RPC (словарь или список).
        :param call_id: Идентификатор вызова.
        :param version: Версия JSON-RPC.
        :return: JSON-строка для тела запроса.
        :raises ValueError: Если параметры не являются словарем, списком или None.
        """
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
    def _create_headers() -> Dict[str, str]:
        """
        Создает заголовки для HTTP-запроса.

        :return: Словарь с заголовками.
        """
        return {"Content-Type": "application/json"}


class WebSocketTransport(Transport):
    """
    Реализация транспорта для выполнения JSON-RPC вызовов через WebSocket (заглушка).
    """

    def call(self, scheme: str, host: str, port: int, url: str, method: str, params: Optional[Union[Dict[str, Any], List[Any]]],
             call_id: int, version: str, certfile: Optional[str] = None, keyfile: Optional[str] = None) -> Dict[str, Any]:
        """
        Выполняет JSON-RPC вызов через WebSocket (заглушка).

        :param scheme: Протокол (ws или wss).
        :param host: Хост.
        :param port: Порт.
        :param url: Относительный URL-путь для вызова.
        :param method: Имя метода JSON-RPC.
        :param params: Параметры метода JSON-RPC (словарь или список).
        :param call_id: Идентификатор вызова.
        :param version: Версия JSON-RPC.
        :param certfile: Путь к файлу сертификата (опционально).
        :param keyfile: Путь к файлу ключа (опционально).
        :return: Ответ от сервера в виде словаря.
        """
        print(f"WebSocket call to {scheme}://{host}:{port}")
        return {"jsonrpc": "2.0", "result": "pong", "id": 1}


class UrlParser:
    """
    Класс для парсинга URL.
    """

    def __init__(self, url: str):
        """
        Инициализирует парсер URL.

        :param url: URL для парсинга.
        """
        self.url = url
        self.parsed_url = urlparse(url)

    @property
    def scheme(self) -> str:
        """
        Возвращает схему URL (например, http, https).

        :return: Схема URL.
        """
        return self.parsed_url.scheme.lower()

    @property
    def host(self) -> Optional[str]:
        """
        Возвращает хост URL.

        :return: Хост URL или None, если хост не указан.
        """
        return self.parsed_url.hostname

    @property
    def port(self) -> Optional[int]:
        """
        Возвращает порт URL.

        :return: Порт URL или None, если порт не указан.
        """
        return self.parsed_url.port

    @property
    def path(self) -> str:
        """
        Возвращает путь URL.

        :return: Путь URL.
        """
        return self.parsed_url.path


class VersionValidator:
    """
    Класс для валидации версии JSON-RPC.
    """

    @staticmethod
    def validate(version: str) -> str:
        """
        Проверяет, поддерживается ли версия JSON-RPC.

        :param version: Версия JSON-RPC.
        :return: Валидная версия JSON-RPC.
        :raises ValueError: Если версия не поддерживается.
        """
        if version not in ('2.0',):
            raise ValueError(f'Version "{version}" is not supported')
        return version


class JrpcServer:
    """
    Класс для выполнения JSON-RPC вызовов на сервере.
    """

    def __init__(self, url: str, version: str, transport: Transport, certfile: Optional[str] = None,
                 keyfile: Optional[str] = None):
        """
        Инициализирует JSON-RPC сервер.

        :param url: URL сервера.
        :param version: Версия JSON-RPC.
        :param transport: Транспорт для выполнения вызовов.
        :param certfile: Путь к файлу сертификата (опционально).
        :param keyfile: Путь к файлу ключа (опционально).
        """
        self.url_parser = UrlParser(url)
        self.version = VersionValidator.validate(version)
        self.transport = transport
        self.certfile = certfile
        self.keyfile = keyfile

    def call_method(self, method: str, params: Optional[Union[Dict[str, Any], List[Any]]] = None, call_id: int = 1) -> Dict[str, Any]:
        """
        Выполняет JSON-RPC вызов на сервере.

        :param method: Имя метода JSON-RPC.
        :param params: Параметры метода JSON-RPC (словарь или список).
        :param call_id: Идентификатор вызова.
        :return: Ответ от сервера в виде словаря.
        """
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