from django.apps import AppConfig


class JrpcClientConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jrpc_client'
    verbose_name = 'Json RPC клиент'
    verbose_name_plural = 'Json RPC клиенты'
