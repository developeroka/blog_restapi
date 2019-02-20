from django import forms
from django.contrib.auth.models import User
from rest.models import ApiToken


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'password')


class TokenForm(forms.ModelForm):
    class Meta:
        model = ApiToken
        fields = ('token_clientId',)
