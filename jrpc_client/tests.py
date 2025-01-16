from django.test import TestCase, RequestFactory
from django.urls import reverse


class JrpcClientViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url = reverse('jrpc_client')

    def test_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'jrpc_client/client.html')

    def test_post_request_with_valid_data(self):
        valid_data = {
            'method': 'some_method',
            'params': 'some_params'
        }
        response = self.client.post(self.url, data=valid_data)
        self.assertEqual(response.status_code, 200)


    def test_post_request_with_invalid_data(self):
        invalid_data = {
            'method': '',
            'params': 'some_params'
        }
        response = self.client.post(self.url, data=invalid_data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('method', response.json())