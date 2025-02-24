import collections
import typing
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import User
from django.db.models import Max
from django.db.models import OuterRef
from django.db.models import Q
from django.db.models import Subquery
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.decorators.http import require_GET

from .errors import Http302
from .forms import GameForm
from .forms import SelectionForm

from .models import Game
from .models import Question
from .models import Selection
from . import utils
from .utils import AuthenticatedHttpRequest


@login_not_required
def health_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok")


@require_GET
def index_view(request: AuthenticatedHttpRequest) -> HttpResponse:
    form = GameForm(request.GET or None)
    if form.is_valid():
        game = Game.objects.filter(slug=form.cleaned_data["slug"]).get()
        game.users.add(request.user)
        return HttpResponseRedirect(reverse("game-detail", kwargs={"slug": game.slug}))
    return render(request, "forcedfun/index.html", {"form": form})


@login_not_required
def register_view(request: HttpRequest) -> HttpResponse:
    form = UserCreationForm[User](request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        next_param = request.GET.get("next", "")
        url_is_safe = url_has_allowed_host_and_scheme(
            url=next_param,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
        redirect_to = next_param if url_is_safe else reverse("index")
        return HttpResponseRedirect(redirect_to)
    return render(request, "forcedfun/register.html", {"form": form})


@require_GET
def game_detail_view(request: AuthenticatedHttpRequest, slug: str) -> HttpResponse:
    game = get_object_or_404(Game, slug=slug)
    utils.user_in_game_check_or_302(request, game, redirect_to=reverse("index"))
    sum_filter = Q(selections__question__game=game)
    users = game.users.order_by("username").annotate(
        points=Coalesce(Sum("selections__points", filter=sum_filter), 0)
    )
    ordered_questions = game.questions.order_by("points", "id")
    questions = list(
        ordered_questions.exclude(scored_at__isnull=True).select_related("respondent")
    )
    latest_scored_at = ordered_questions.filter(scored_at__isnull=False).aggregate(
        latest_scored_at=Max("scored_at")
    )["latest_scored_at"]
    delta = timezone.now() - (latest_scored_at or timezone.now())
    next_question = (
        ordered_questions.filter(scored_at__isnull=True)
        .select_related("respondent")
        .first()
    )
    if latest_scored_at is None and next_question is not None:  # pragma: no cover
        # if it's the first question, always show it
        questions.append(next_question)
    elif delta > timedelta(seconds=3600) and next_question:  # pragma: no cover
        # if it's the second question, make sure it's been 12 hours since the last question was complete
        questions.append(next_question)

    context = {
        "game": game,
        "questions": questions,
        "users": users,
    }
    return render(request, "forcedfun/game_detail.html", context)


@require_GET
def question_detail_view(request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
    question = get_object_or_404(Question, pk=pk)
    utils.user_in_game_check_or_302(
        request, question.game, redirect_to=reverse("index")
    )
    # if selection does not exists for this player then redirect to selection create
    check = (
        question.scored_at is None
        and not Selection.objects.filter(question=question, user=request.user).exists()
    )
    utils.check_or_302(
        check,
        redirect_to=reverse("selection-create", kwargs={"question_pk": question.pk}),
    )

    respondent_selection = Selection.objects.filter(
        question=question, user=question.respondent
    ).first()

    question_selections = (
        Selection.objects.filter(question=question)
        .exclude(user=question.respondent)
        .filter(user=OuterRef("pk"))
    )
    game = question.game
    users = game.users.exclude(id=question.respondent_id).annotate(
        option_text=Subquery(question_selections[:1].values("option_text")),
        option_idx=Subquery(question_selections[:1].values("option_idx")),
    )
    option_pcts = []
    option_idx_list = [user.option_idx for user in users if user.option_idx is not None]
    n_option_idx_list = len(option_idx_list)
    question_selections_exist = bool(n_option_idx_list)
    counter = collections.Counter(option_idx_list)
    for i, _ in enumerate(question.options):
        value = counter.get(i, 0)
        try:
            pct = (value / n_option_idx_list) * 100
        except ZeroDivisionError:
            pct = 0
        option_pcts.append(round(pct))

    context = {
        "respondent_selection": respondent_selection,
        "users": users,
        "game": game,
        "question": question,
        "option_pcts": option_pcts,
        "question_selections_exist": question_selections_exist,
    }
    return render(request, "forcedfun/question_detail.html", context)


class QuestionScoreView(UserPassesTestMixin, View):
    def test_func(self) -> bool:
        return self.request.user.is_superuser

    def get_respodent_selection_or_302(
        self, request: AuthenticatedHttpRequest, question: Question
    ) -> Selection:
        try:
            respondent_selection = question.selections.get(user=question.respondent)
        except Selection.DoesNotExist:
            messages.warning(
                request, "Unable to score. Respondent selection not found."
            )
            raise Http302(reverse("question-detail", kwargs={"pk": question.pk}))

        return respondent_selection

    def get_selections_or_302(
        self, request: AuthenticatedHttpRequest, question: Question
    ) -> typing.Sequence[Selection]:
        selections = list(question.selections.exclude(user=question.respondent))
        if len(selections) == 0:
            messages.warning(
                request, "Unable to score. No non-respondent selections found"
            )
            raise Http302(reverse("question-detail", kwargs={"pk": question.pk}))

        return selections

    def post(self, request: AuthenticatedHttpRequest, pk: int) -> HttpResponse:
        question = get_object_or_404(Question, pk=pk)
        respondent_selection = self.get_respodent_selection_or_302(request, question)
        selections = self.get_selections_or_302(request, question)
        scored_selections = utils.score_selections(
            selections=selections,
            respondent_selection=respondent_selection,
            points=question.points,
        )
        Selection.objects.bulk_update(scored_selections, fields=["points"])
        question.scored_at = timezone.now()
        question.save(update_fields=["scored_at"])
        return HttpResponseRedirect(
            reverse("question-detail", kwargs={"pk": question.pk})
        )


class SelectionCreateView(View):
    template_name = "forcedfun/selection_create.html"

    def get_context_data(self, question: Question) -> dict[str, typing.Any]:
        options_forms = []
        for i, option in enumerate(question.options):
            form = SelectionForm(initial={"option_idx": i, "option_text": option})
            options_forms.append((option, form))

        context = {
            "game": question.game,
            "question": question,
            "options_forms": options_forms,
        }
        return context

    def get(self, request: AuthenticatedHttpRequest, question_pk: int) -> HttpResponse:
        question = get_object_or_404(Question, pk=question_pk)
        utils.user_in_game_check_or_302(
            request, question.game, redirect_to=reverse("index")
        )
        # if selection already exists for this player for this question then redirect to question detail
        utils.check_or_302(
            Selection.objects.filter(question=question, user=request.user).exists(),
            redirect_to=reverse("question-detail", kwargs={"pk": question.pk}),
        )
        context = self.get_context_data(question)
        return render(request, self.template_name, context)

    def get_scored_selections(
        self,
        score_question: bool,
        selections: typing.Sequence[Selection],
        respondent_selection: Selection,
        question: Question,
    ) -> typing.Sequence[Selection]:
        if not score_question:
            return []

        selections = utils.score_selections(
            selections=selections,
            respondent_selection=respondent_selection,
            points=question.points,
        )
        return selections

    def perform_score_question(
        self, scored_selections: typing.Sequence[Selection], question: Question
    ) -> Question:
        if scored_selections:  # pragma: no branch
            Selection.objects.bulk_update(scored_selections, fields=["points"])
            question.scored_at = timezone.now()
            question.save(update_fields=["scored_at"])

        return question

    def post(self, request: AuthenticatedHttpRequest, question_pk: int) -> HttpResponse:
        question = get_object_or_404(Question, pk=question_pk)
        utils.user_in_game_check_or_302(
            request, question.game, redirect_to=reverse("index")
        )
        utils.check_or_302(
            Selection.objects.filter(question=question, user=request.user).exists(),
            redirect_to=reverse("question-detail", kwargs={"pk": question.pk}),
        )
        form = SelectionForm(request.POST or None)
        if form.is_valid():
            Selection.objects.create(
                user=request.user,
                question=question,
                option_idx=form.cleaned_data["option_idx"],
                option_text=form.cleaned_data["option_text"],
            )
            question.save_answer_fields(
                answer_idx=form.cleaned_data["option_idx"],
                answer_text=form.cleaned_data["option_idx"],
                is_respondent=question.respondent == request.user,
            )

            respondent_selection = question.selections.filter(
                user=question.respondent,
            ).first()
            selections = question.selections.exclude(
                user=question.respondent,
            )
            score_question = bool(
                respondent_selection
                and question.selections.count() == question.game.users.count()
                and selections.count() > 0
            )
            scored_selections = self.get_scored_selections(
                score_question=score_question,
                selections=list(selections),
                respondent_selection=typing.cast(Selection, respondent_selection),
                question=question,
            )
            question = self.perform_score_question(scored_selections, question)
            return HttpResponseRedirect(
                reverse("question-detail", kwargs={"pk": question.pk})
            )

        context = self.get_context_data(question)
        return render(request, self.template_name, context)
