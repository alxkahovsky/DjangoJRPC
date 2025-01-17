import json
import logging
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.conf import settings
from .forms import JrpcClientForm
from .client import JrpcServer, http_transport

logger = logging.getLogger(__name__)


class JrpcClientView(View):
    template_name = 'jrpc_client/client.html'
    jrpc_url = "https://slb.medv.ru/api/v2/"
    jrpc_server = JrpcServer
    jrpc_transport = http_transport
    jrpc_cert = settings.JRPC_CERT
    jrpc_key = settings.JRPC_KEY
    form = JrpcClientForm

    def get(self, request, *args, **kwargs):
        """
        Обрабатывает GET-запрос и отображает форму.
        """
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """
        Обрабатывает POST-запрос, выполняет JSON-RPC вызов и возвращает результат.
        """
        form = self.form(request.POST)
        if not form.is_valid():
            return JsonResponse(status=400, data=form.errors, safe=False)

        server = self.jrpc_server(self.jrpc_url, "2.0", self.jrpc_transport,
                                  self.jrpc_cert, self.jrpc_key)

        try:
            response = server.call_method(
                form.cleaned_data['method'],
                json.loads(form.cleaned_data['params']) if form.cleaned_data['params'] else None
            )

            if 'error' in response:
                error_data = response['error']
                error_message = self._decode_jrpc_error(
                    error_data)
                logger.error(f"JSON-RPC Error: {error_message}."
                             f" Original response: {json.dumps(response)}")
                return JsonResponse(status=400, data={'error': error_message}, safe=False)

            logger.info(f"JSON-RPC Response: {json.dumps(response)}")
            return JsonResponse(status=200, data=response, safe=False)

        except Exception as e:
            # Логируем исключение и возвращаем ошибку
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return JsonResponse(status=500, data={'error': 'Internal Server Error'}, safe=False)

    @staticmethod
    def _decode_jrpc_error(error_data: dict) -> str:
        """
        Расшифровывает ошибку JSON-RPC и возвращает понятное сообщение.

        :param error_data: Словарь с данными об ошибке из JSON-RPC ответа.
        :return: Расшифрованное сообщение об ошибке.
        """
        error_code = error_data.get('code', -1)
        error_message = error_data.get('message', 'Unknown error')
        error_details = error_data.get('data', {})

        if error_code == -32700:
            return "Parse error: Invalid JSON was received by the server."
        elif error_code == -32600:
            return "Invalid Request: The JSON sent is not a valid Request object."
        elif error_code == -32601:
            return "Method not found: The method does not exist or is not available."
        elif error_code == -32602:
            return "Invalid params: Invalid method parameter(s)."
        elif error_code == -32603:
            return "Internal error: Internal JSON-RPC error."
        elif -32099 <= error_code <= -32000:
            return f"Server error: {error_message}. Details: {error_details}"
        else:
            return f"Unknown error: {error_message}. Details: {error_details}"
