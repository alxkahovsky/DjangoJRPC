from django.shortcuts import render
from django.views import View
from .forms import JrpcClientForm
from django.http import JsonResponse


class JrpcClientView(View):
    template_name = 'jrpc_client/client.html'
    jrpc_server = None
    form = JrpcClientForm

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {})


    def post(self, request, *args, **kwargs):
        form = self.form(request.POST)
        if form.is_valid():
            server = self.jrpc_server
            print(form.cleaned_data['method'], form.cleaned_data['params'])
            return JsonResponse(status=200, data={'response': 'ok'})
        return JsonResponse(status=400, data=form.errors)
