import json
from types import NoneType

from django import forms
from django.core.exceptions import ValidationError


class JrpcClientForm(forms.Form):
    method = forms.CharField(label='Имя метода', max_length=100, required=True)
    params = forms.CharField(label="Параметры", widget=forms.Textarea, max_length=1000, required=False)

    def clean_params(self):
        params = self.cleaned_data.get('params')
        if params:
            try:
                json.loads(params)
            except json.JSONDecodeError:
                raise ValidationError("Params must be a JSON format.")
            if not isinstance(params, (dict, list, NoneType)):
                raise ValidationError(f'Params "{params}" are invalid')
        return params
