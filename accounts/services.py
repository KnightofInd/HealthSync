from django.db import transaction

from .models import User


@transaction.atomic
def register_user(*, name: str, email: str, password: str) -> User:
	return User.objects.create_user(name=name, email=email, password=password)
