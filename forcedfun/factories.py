import typing
from datetime import datetime

from django.contrib.auth.models import User

from .models import Game
from .models import Question
from .models import Selection


def user_factory(
    username: str = "userdefault", password: str = "password", **kwargs: typing.Any
) -> User:
    return User.objects.create_user(
        username=username,
        password=password,
        **kwargs,
    )


def selection_factory(
    user: User | None = None,
    question: Question | None = None,
    option_text: str = "optiondefault",
    option_idx: int = 0,
    points: int | None = None,
) -> Selection:
    user = user or user_factory()
    return Selection.objects.create(
        user=user,
        question=question or question_factory(respondent=user),
        option_text=option_text,
        option_idx=option_idx,
        points=points,
    )


def game_factory(slug: str = "gamedefault", users: typing.Sequence[User] = ()) -> Game:
    game = Game.objects.create(slug=slug)
    game.users.add(*users)
    return game


def question_factory(
    game: Game | None = None,
    respondent: User | None = None,
    options: typing.Sequence[str] = ("option1", "option2"),
    points: int = 1,
    answer_idx: int | None = None,
    answer_text: str = "",
    scored_at: datetime | None = None,
) -> Question:
    respondent = respondent or user_factory()
    return Question.objects.create(
        game=game or game_factory(users=(respondent,)),
        respondent=respondent,
        options=options,
        points=points,
        scored_at=scored_at,
        answer_idx=answer_idx,
        answer_text=answer_text,
    )
