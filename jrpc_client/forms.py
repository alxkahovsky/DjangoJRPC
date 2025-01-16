from django import forms


class JrpcClientForm(forms.Form):
    method = forms.CharField(label='Имя метода', max_length=100, required=True)
    params = forms.CharField(label="Параметры", widget=forms.Textarea, max_length=1000, required=False)
