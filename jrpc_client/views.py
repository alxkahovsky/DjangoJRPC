import json
from django.shortcuts import render
from django.views import View
from .forms import JrpcClientForm
from django.http import JsonResponse
from .client import JrpcServer, http_transport
from django.conf import settings


class JrpcClientView(View):
    template_name = 'jrpc_client/client.html'
    jrpc_url = "https://slb.medv.ru/api/v2/"
    jrpc_server = JrpcServer
    jrpc_transport = http_transport
    jrpc_cert = settings.JRPC_CERT
    jrpc_key = settings.JRPC_KEY
    form = JrpcClientForm


    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)


    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        if form.is_valid():
            # ToDo обработка кодов ошибок от JRPC
            server = self.jrpc_server(self.jrpc_url, "2.0", self.jrpc_transport, self.jrpc_cert, self.jrpc_key)
            response = server.call_method(
                form.cleaned_data['method'],
                json.loads(form.cleaned_data['params']) if form.cleaned_data['params'] else None)
            return JsonResponse(status=200, data=str(response), safe=False)
        return JsonResponse(status=400, data=form.errors)
