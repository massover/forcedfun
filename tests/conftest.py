import pytest


@pytest.fixture()
def anonymous_client(client):
    return client


@pytest.fixture()
def user_client(db, user, client):
    client.force_login(user)
    return client


@pytest.fixture()
def user(db):
    from django.contrib.auth.models import User

    user = User.objects.create_user(username="user", password="password")
    return user
