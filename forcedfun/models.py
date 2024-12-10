from django.contrib.postgres.fields import ArrayField
from django import forms
from django.db import models
from django.db.models import UniqueConstraint


class TextInputTextField(models.TextField):  # type: ignore
    def formfield(self, form_class=None, choices_form_class=None, **kwargs):  # type: ignore
        kwargs["widget"] = forms.TextInput()
        return super().formfield(
            form_class=form_class, choices_form_class=choices_form_class, **kwargs
        )


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True


class Selection(BaseModel):
    user = models.ForeignKey("auth.User", on_delete=models.DO_NOTHING)
    question = models.ForeignKey("forcedfun.Question", on_delete=models.DO_NOTHING)
    option_text = TextInputTextField()
    option_idx = models.PositiveSmallIntegerField()
    points = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.option_text=}, {self.user_id=}, {self.question_id=}"

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["user", "question"], name="selection_user_question_unique"
            )
        ]
        default_related_name = "selections"


class Question(BaseModel):
    respondent = models.ForeignKey("auth.User", on_delete=models.DO_NOTHING)
    game = models.ForeignKey("forcedfun.Game", on_delete=models.DO_NOTHING)
    options = ArrayField(models.TextField(), max_length=2)
    answer_idx = models.PositiveSmallIntegerField(null=True, blank=True)
    answer_text = TextInputTextField(default="", blank=True)
    points = models.PositiveSmallIntegerField()
    scored_at = models.DateTimeField(default=None, null=True, blank=True)

    class Meta:
        default_related_name = "questions"
        ordering = [
            "id",
        ]

    def save_answer_fields(
        self, answer_idx: int, answer_text: str, is_respondent: bool
    ) -> None:
        if not is_respondent:
            return

        self.answer_idx = answer_idx
        self.answer_text = answer_text
        self.save(update_fields=["answer_idx", "answer_text"])


class Game(BaseModel):
    slug = models.SlugField()
    users = models.ManyToManyField("auth.User", blank=True)

    def __str__(self) -> str:
        return self.slug

    class Meta:
        constraints = [UniqueConstraint(fields=["slug"], name="game_slug_unique")]
        default_related_name = "games"
