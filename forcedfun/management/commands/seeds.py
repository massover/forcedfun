import typing

from django.contrib.auth.models import User
from django.core.management import BaseCommand

from forcedfun.models import Game
from forcedfun.models import Question


def seed_user(username: str, password: str) -> User:
    if not User.objects.filter(username=username).exists():
        return User.objects.create_superuser(username=username, password=password)
    return User.objects.get(username=username)


class Command(BaseCommand):
    def handle(self, *args: typing.Any, **option: typing.Any) -> None:
        seed_user(username="admin", password="password")
        june = seed_user(username="june", password="password")
        bruce = seed_user(username="bruce", password="password")
        respondent = seed_user(username="respondent", password="password")
        game, _ = Game.objects.get_or_create(slug="game1")
        game.users.add(june, bruce, respondent)
        if Question.objects.count() == 0:
            Question.objects.create(
                game=game,
                respondent=respondent,
                options=[
                    "Witness the beginning of planet Earth",
                    "Witness the end of planet Earth",
                ],
                points=1,
            )
