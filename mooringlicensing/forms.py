from __future__ import unicode_literals
from django.contrib.auth import get_user_model
from django.forms import Form, EmailField

User = get_user_model()

class LoginForm(Form):
    email = EmailField(max_length=254)