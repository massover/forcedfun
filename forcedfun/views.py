import typing

from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Max
from django.db.models import OuterRef
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
    users = game.users.order_by("username").annotate(
        points=Coalesce(Sum("selections__points"), 0)
    )
    ordered_questions = game.questions.order_by("points", "id")
    questions = list(ordered_questions.exclude(scored_at__isnull=True).all())
    latest_scored_at = ordered_questions.filter(scored_at__isnull=False).aggregate(
        latest_scored_at=Max("scored_at")
    )["latest_scored_at"]
    delta = timezone.now() - (latest_scored_at or timezone.now())
    next_question = ordered_questions.filter(scored_at__isnull=True).first()
    if latest_scored_at is None and next_question is not None:  # pragma: no cover
        # if it's the first question, always show it
        questions.append(next_question)
    elif (delta.seconds // 3600) > 12 and next_question:  # pragma: no cover
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

    context = {
        "respondent_selection": respondent_selection,
        "users": users,
        "game": game,
        "question": question,
    }
    return render(request, "forcedfun/question_detail.html", context)


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
