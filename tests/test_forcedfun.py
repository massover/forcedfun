import pytest
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


# @pytest.mark.django_db
# class TestScoreSelection:
# def test_set_points(self):
#     selections = [
#         Selection(option_idx=0),
#         Selection(option_idx=1),
#         Selection(option_idx=0),
#     ]
#     respondent_selection = [
#         Selection(option_idx=0),
#     ]
#
#
# def test_user_selections_get_points_from_respondent_answer(self):
#     game = factories.game_factory()
#     respondent = factories.user_factory(username="respondent")
#     user1 = factories.user_factory(username="user1")
#     options = ("option1", "option2")
#     question = factories.question_factory(
#         respondent=respondent,
#         game=game,
#         options=options,
#         points=1,
#         answer_idx=0,
#         answer_text=options[0],
#     )
#     respondent_selection = factories.selection_factory(
#         user=respondent,
#         question=question,
#         option_idx=0,
#         option_text=question.options[0],
#         points=None,
#     )
#     user1_selection = factories.selection_factory(
#         user=user1,
#         question=question,
#         option_idx=0,
#         option_text=question.options[0],
#         points=None,
#     )
#
#     user2 = factories.user_factory(username="user2")
#     user2_selection = factories.selection_factory(
#         user=user2,
#         question=question,
#         option_idx=1,
#         option_text=question.options[1],
#         points=None,
#     )
#     question.score_selections()
#     respondent_selection.refresh_from_db()
#     user1_selection.refresh_from_db()
#     user2_selection.refresh_from_db()
#
#
#     assert respondent_selection.points == 1
#     assert user1_selection.points == 1
#     assert user2_selection.points == 0
#
# def test_respondent_selection_gets_no_points_if_less_than_half_match(self):
#     game = factories.game_factory()
#     respondent = factories.user_factory(username="respondent")
#     user1 = factories.user_factory(username="user1")
#
#     options = ("option1", "option2")
#     question = factories.question_factory(
#         respondent=respondent,
#         game=game,
#         options=options,
#         points=1,
#         answer_idx=0,
#         answer_text=options[0],
#     )
#
#     respondent_selection = factories.selection_factory(
#         user=respondent,
#         question=question,
#         option_idx=0,
#         option_text=question.options[0],
#         points=None,
#     )
#     user1_selection = factories.selection_factory(
#         user=user1,
#         question=question,
#         option_idx=0,
#         option_text=question.options[0],
#         points=None,
#     )
#
#     user2 = factories.user_factory(username="user2")
#     user2_selection = factories.selection_factory(
#         user=user2,
#         question=question,
#         option_idx=1,
#         option_text=question.options[1],
#         points=None,
#     )
#     user3 = factories.user_factory(username="user3")
#     user3_selection = factories.selection_factory(
#         user=user3,
#         question=question,
#         option_idx=1,
#         option_text=question.options[1],
#         points=None,
#     )
#
# a
#     question.score_selections()
#     respondent_selection.refresh_from_db()
#     user1_selection.refresh_from_db()
#     user2_selection.refresh_from_db()
#     user3_selection.refresh_from_db()
#
#     assert respondent_selection.points == 0
#     assert user1_selection.points == 1
#     assert user2_selection.points == 0
#     assert user3_selection.points == 0
