import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.http import Http404
from django.http import HttpResponse

from forcedfun import factories
from forcedfun.errors import Http302
from forcedfun.middleware import RedirectMiddleware
from forcedfun.models import Question
from forcedfun.models import Selection
from forcedfun import utils
from forcedfun.forms import GameForm
from forcedfun.settings.utils import getbool


def test_for_cov():
    import forcedfun.settings.production  # noqa: F401
    import forcedfun.settings.local  # noqa: F401
    import forcedfun.wsgi  # noqa: F401


@pytest.mark.django_db
def test_seeds():
    call_command("seeds")
    # idempotent
    call_command("seeds")


class TestGameForm:
    @pytest.mark.django_db
    def test_clean_slug(self):
        form = GameForm()
        form.cleaned_data = {"slug": "does-not-exist"}
        with pytest.raises(ValidationError):
            form.clean_slug()


class TestQuestion:
    def test_save_answer_fields_for_non_respondent(self):
        question = Question(answer_idx=None, answer_text="")
        question.save_answer_fields(
            answer_idx=1, answer_text="text", is_respondent=False
        )
        assert question.answer_text == ""
        assert question.answer_idx is None

    @pytest.mark.django_db
    def test_save_answer_fields_on_respondent_request(self):
        question = factories.question_factory(answer_idx=None, answer_text="")
        question.save_answer_fields(
            answer_idx=1, answer_text="text", is_respondent=True
        )
        question.refresh_from_db()
        assert question.answer_text == "text"
        assert question.answer_idx == 1


def test_redirect_middleware():
    def get_response(request):
        return HttpResponse()

    middleware = RedirectMiddleware(get_response)
    response = middleware(None)
    assert response.status_code == 200

    response = middleware.process_exception(None, Http302("url"))
    assert response.status_code == 302

    response = middleware.process_exception(None, Http404())
    assert response is None


def test_check_or_302():
    with pytest.raises(Http302):
        utils.check_or_302(True, redirect_to="index")

    utils.check_or_302(False, redirect_to="index")


def test_getbool():
    assert getbool("TEST", environ={"TEST": "t"}) is True
    assert getbool("TEST", environ={"TEST": "false"}) is False
    assert getbool("TEST", False) is False


class TestScoreSelections:
    def test_score_selections_updates_points_from_respondent_answer(self):
        selection0 = Selection(option_idx=0)
        selection1 = Selection(option_idx=1)
        selection2 = Selection(option_idx=1)
        respondent_selection = Selection(option_idx=0)

        selections = [selection0, selection1, selection2]
        utils.score_selections(
            selections=selections,
            respondent_selection=respondent_selection,
            points=1,
        )
        assert selection0.points == 1
        assert selection1.points == 0
        assert selection2.points == 0
        assert respondent_selection.points == 0

    def test_respondent_answer_points_when_half_or_more_match(self):
        selection0 = Selection(option_idx=0)
        selection1 = Selection(option_idx=1)
        selection2 = Selection(option_idx=0)
        respondent_selection = Selection(option_idx=0)

        selections = [selection0, selection1, selection2]
        utils.score_selections(
            selections=selections,
            respondent_selection=respondent_selection,
            points=1,
        )
        assert selection0.points == 1
        assert selection1.points == 0
        assert selection2.points == 1
        assert respondent_selection.points == 1


@pytest.mark.django_db
def test_user_in_game_check_or_302(user, authenticated_request):
    game = factories.game_factory(users=())
    authenticated_request.user = User()
    with pytest.raises(Http302):
        utils.user_in_game_check_or_302(
            authenticated_request, game, redirect_to="index"
        )

    # happy path does not explode
    game.users.add(user)
    authenticated_request.user = user
    utils.user_in_game_check_or_302(authenticated_request, game, redirect_to="index")
