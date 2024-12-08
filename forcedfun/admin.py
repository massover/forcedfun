from django.contrib import admin
from forcedfun.models import Game
from forcedfun.models import Question
from forcedfun.models import Selection


class QuestionInline(admin.StackedInline[Question, Game]):
    extra = 1
    model = Question
    autocomplete_fields = ["respondent", "game"]


@admin.register(Game)
class GameAdmin(admin.ModelAdmin[Game]):
    list_display = ["id", "slug", "created_at"]
    search_fields = ["slug", "id"]
    inlines = [QuestionInline]
    filter_horizontal = [
        "users",
    ]


@admin.register(Selection)
class SelectionAdmin(admin.ModelAdmin[Selection]):
    list_display = ["id", "option_text", "option_idx", "question", "user", "points"]
    search_fields = ["user__id", "question__id"]
    autocomplete_fields = ["user", "question"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin[Question]):
    list_display = [
        "id",
        "respondent",
        "game",
        "options",
        "points",
        "answer_idx",
        "answer_text",
    ]
    autocomplete_fields = ["respondent", "game"]
    search_fields = ["id", "answer_text"]
