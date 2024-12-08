from django import forms
from django import forms
from django import forms
from django import forms
from django import forms
from django import forms
from django import forms
from django.core.exceptions import ValidationError

from forcedfun.models import Game


class SelectionForm(forms.Form):
    option_idx = forms.IntegerField(widget=forms.HiddenInput())
    option_text = forms.CharField(widget=forms.HiddenInput())


class GameForm(forms.Form):
    slug = forms.SlugField()

    def clean_slug(self) -> str:
        slug: str = self.cleaned_data["slug"]
        if not Game.objects.filter(slug=slug).exists():
            raise ValidationError("Game does not exist")
        return slug
