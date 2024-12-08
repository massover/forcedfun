import typing

from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect

from .errors import Http302


class RedirectMiddleware:
    def __init__(
        self, get_response: typing.Callable[[typing.Any], HttpResponse]
    ) -> None:
        self.get_response = get_response

    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> HttpResponse | None:
        if isinstance(exception, Http302):
            return HttpResponseRedirect(exception.url)
        return None

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)
