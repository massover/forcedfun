import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from forcedfun import factories
from forcedfun.models import Question
from forcedfun.models import Selection
from forcedfun.views import SelectionCreateView


@pytest.mark.parametrize(
    "name",
    [
        "login",
        "register",
        "health",
    ],
)
def test_login_not_required_view_ok(name, client):
    url = reverse(name)
    response = client.get(url)
    assert response.status_code == 200, response.content.decode()


class TestRegisterView:
    def test_get_ok(self, client):
        url = reverse("register")
        response = client.get(url)
        assert response.status_code == 200, response.content.decode()

    @pytest.mark.django_db
    def test_post_ok(self, client):
        data = {
            "username": "user1",
            "password1": "password1",
            "password2": "password1",
        }
        url = reverse("register")
        response = client.post(url, data=data, follow=True)
        assert response.status_code == 200, response.content.decode()
        assert User.objects.count() == 1


class TestIndexView:
    def test_no_url_params(self, user_client):
        url = reverse("index")
        response = user_client.get(url)
        assert response.status_code == 200

    def test_game_slug_in_url(self, user_client):
        game = factories.game_factory()
        url = reverse("index") + f"?slug={game.slug}"
        response = user_client.get(url, follow=True)
        assert response.status_code == 200
        assert game.users.count() == 1


@pytest.mark.parametrize(
    "name, method",
    [
        ("logout", "post"),
        ("index", "get"),
    ],
)
def test_login_required_view_get_ok(name, method, user_client):
    url = reverse(name)
    method = getattr(user_client, method)
    response = method(url, follow=True)
    assert response.status_code == 200, response.content.decode()


class TestGameDetailView:
    def test_ok(self, user_client, user):
        game = factories.game_factory(users=(user,))
        url = reverse("game-detail", kwargs={"slug": game.slug})
        response = user_client.get(url)
        assert response.status_code == 200


class TestQuestionDetailView:
    def test_ok(self, user_client, user):
        question = factories.question_factory(respondent=user)
        factories.selection_factory(user=user, question=question)
        url = reverse("question-detail", kwargs={"pk": question.pk})
        response = user_client.get(url)
        assert response.status_code == 200


class TestSelectionCreateView:
    def test_get_scored_selections_when_it_does_not_need_to_score(self):
        view = SelectionCreateView()
        scored_selections = view.get_scored_selections(False, [], None, None)
        assert not scored_selections

    def test_get_scored_selections_when_it_needs_to_score(self):
        view = SelectionCreateView()
        selection0 = Selection(option_idx=0)
        selection1 = Selection(option_idx=1)
        selection2 = Selection(option_idx=1)
        respondent_selection = Selection(option_idx=0)
        selections = [selection0, selection1, selection2]
        question = Question(points=1)
        scored_selections = view.get_scored_selections(
            True, selections, respondent_selection, question
        )
        assert scored_selections

    @pytest.mark.django_db
    def test_perform_score_question(self):
        selection = factories.selection_factory()
        question = selection.question
        scored_selections = [selection]
        view = SelectionCreateView()
        view.perform_score_question(scored_selections, question)
        question.refresh_from_db()
        assert question.scored_at <= timezone.now()

    def test_get_ok(self, user_client, user):
        question = factories.question_factory(respondent=user)
        url = reverse("selection-create", kwargs={"question_pk": question.pk})
        response = user_client.get(url)
        assert response.status_code == 200

    def test_post_ok(self, user_client, user):
        question = factories.question_factory(respondent=user)
        data = {
            "option_idx": 0,
            "option_text": question.options[0],
        }
        url = reverse("selection-create", kwargs={"question_pk": question.pk})
        response = user_client.post(url, data=data, follow=True)
        assert response.status_code == 200, response.content.decode()
        assert Selection.objects.count() == 1, response.content.decode()

    def test_post_error(self, user_client, user):
        question = factories.question_factory(respondent=user)
        data = {
            "option_idx": 0,
        }
        url = reverse("selection-create", kwargs={"question_pk": question.pk})
        response = user_client.post(url, data=data, follow=True)
        assert response.status_code == 200
        assert Selection.objects.count() == 0
