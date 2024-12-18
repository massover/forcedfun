import typing

from django.contrib.auth.models import User
from django.http import HttpRequest
from django.contrib import messages

from .errors import Http302
from .models import Selection, Game


def score_selections(
    *,
    selections: typing.Sequence[Selection],
    respondent_selection: Selection,
    points: int,
) -> typing.Sequence[Selection]:
    n_correct = 0
    to_update = []
    n_selections = len(selections)
    for selection in selections:
        if selection.option_idx == respondent_selection.option_idx:
            selection.points = points
            n_correct += 1
        else:
            selection.points = 0
        to_update.append(selection)

    if (n_correct / n_selections) >= 0.5:
        respondent_selection.points = points
    else:
        respondent_selection.points = 0

    to_update.append(respondent_selection)
    return to_update


def check_or_302(condition: bool, *, redirect_to: str, message: str = "") -> None:
    if condition:
        raise Http302(redirect_to)


class AuthenticatedHttpRequest(HttpRequest):
    user: User


def user_in_game_check_or_302(
    request: AuthenticatedHttpRequest, game: Game, *, redirect_to: str
) -> None:
    exists = game.users.filter(id=request.user.id).exists()
    if not exists:
        messages.warning(request, f"Please join {game.slug} to continue.")
        raise Http302(redirect_to)
