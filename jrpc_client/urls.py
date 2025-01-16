from django.urls import path
from .views import JrpcClientView


urlpatterns = [
    path('', JrpcClientView.as_view(), name='jrpc_client'),
]
