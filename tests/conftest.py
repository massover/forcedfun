import pytest
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware

from forcedfun.utils import AuthenticatedHttpRequest


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


@pytest.fixture()
def authenticated_request():
    request = AuthenticatedHttpRequest()
    middleware = SessionMiddleware(get_response=lambda request: None)
    middleware(request)
    middleware = MessageMiddleware(get_response=lambda request: None)
    middleware(request)
    return request
