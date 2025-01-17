import json
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.urls import reverse
from .client import JrpcServer, http_transport
from .views import JrpcClientView



class JrpcClientViewTests(TestCase):
    """
    Тесты для представления JrpcClientView.
    """

    def setUp(self) -> None:
        """
        Настройка тестового окружения.
        """
        self.factory = RequestFactory()
        self.url = reverse('jrpc_client')
        self.view: JrpcClientView = JrpcClientView()

    def test_get_request(self) -> None:
        """
        Тестирование GET запроса к JrpcClientView.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jrpc_client/client.html')

    def test_post_request_with_invalid_method(self) -> None:
        """
        Тестирование POST запроса с невалидным методом.
        """
        invalid_data = {
            'method': '',
            'params': 'some_params'
        }
        response = self.client.post(self.url, data=invalid_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('method', response.json())

    def test_post_request_with_invalid_params(self) -> None:
        """
        Тестирование POST запроса с невалидными параметрами.
        """
        invalid_data = {
            'method': 'ping',
            'params': '123'
        }
        response = self.client.post(self.url, data=invalid_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('params', response.json())

    @patch('jrpc_client.views.JrpcServer.call_method')
    def test_post_method_success(self, mock_jrpc_call: MagicMock) -> None:
        """
        Тестирует успешный вызов jsonrpc метода через POST запрос.

        Args:
            mock_jrpc_call (MagicMock): Мок объекта вызова jsonrpc метода.
        """
        mock_jrpc_call.return_value = {
            'result': {
                '_data': {
                    'user': {
                        'id': 1,
                    }
                }
            }
        }
        data = {'method': 'auth.check', 'params': ''}
        request = self.factory.post(self.url, data=data)
        response = self.view.post(request)
        json_response = json.loads(response.content.decode('utf-8'))
        user_data = json_response['result']['_data']['user']
        self.assertEqual(response.status_code, 200)
        self.assertIn('result', json_response)
        self.assertEqual(user_data['id'], 1)


class TestJrpcServer(unittest.TestCase):
    """
    Тесты для класса JrpcServer.
    """

    def setUp(self) -> None:
        """
        Настройка тестового окружения.
        """
        self.http_url = "http://example.com/api"
        self.https_url = "https://example.com/api"
        self.version = "2.0"
        self.http_transport = http_transport

    @patch('http.client.HTTPConnection')
    def test_http_call_method(self, mock_http_conn: MagicMock) -> None:
        """
        Тестирование вызова метода через HTTP.

        Args:
            mock_http_conn (MagicMock): Мок HTTP соединения.
        """
        mock_conn = MagicMock()
        mock_http_conn.return_value = mock_conn
        mock_conn.getresponse.return_value.read.return_value = b'{"jsonrpc": "2.0", "result": "success", "id": 1}'

        server = JrpcServer(self.http_url, self.version, self.http_transport)

        response = server.call_method("test_method", {"param": "value"})

        self.assertEqual(response, {"jsonrpc": "2.0", "result": "success", "id": 1})
        mock_http_conn.assert_called_once()
        mock_conn.request.assert_called_once_with(
            "POST", "/api",
            body='{"jsonrpc": "2.0", "method": "test_method", "params": {"param": "value"}, "id": 1}',
            headers={"Content-Type": "application/json"}
        )

    @patch('http.client.HTTPSConnection')
    def test_https_call_method(self, mock_https_conn: MagicMock) -> None:
        """
        Тестирование вызова метода через HTTPS.

        Args:
            mock_https_conn (MagicMock): Мок HTTPS соединения.
        """
        mock_conn = MagicMock()
        mock_https_conn.return_value = mock_conn
        mock_conn.getresponse.return_value.read.return_value = b'{"jsonrpc": "2.0", "result": "success", "id": 1}'

        server = JrpcServer(self.https_url, self.version, self.http_transport)

        response = server.call_method("test_method", {"param": "value"})

        self.assertEqual(response, {"jsonrpc": "2.0", "result": "success", "id": 1})
        mock_https_conn.assert_called_once()
        mock_conn.request.assert_called_once_with(
            "POST", "/api",
            body='{"jsonrpc": "2.0", "method": "test_method", "params": {"param": "value"}, "id": 1}',
            headers={"Content-Type": "application/json"}
        )

    def test_invalid_version(self) -> None:
        """
        Тестирование вызова с неверной версией JSON-RPC.
        """
        with self.assertRaises(ValueError) as context:
            JrpcServer(self.http_url, "1.0", self.http_transport)
        self.assertEqual(str(context.exception), 'Version "1.0" is not supported')

    def test_invalid_scheme(self) -> None:
        """
        Тестирование вызова с неверной схемой URL.
        """
        with self.assertRaises(ValueError) as context:
            server = JrpcServer("ftp://example.com/api", self.version, self.http_transport)
            server.call_method("test_method", {"param": "value"})
        self.assertEqual(str(context.exception), 'Scheme "ftp" is not supported. Use "http" or "https".')


if __name__ == '__main__':
    unittest.main()
