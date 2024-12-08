from django.urls import reverse

from forcedfun import models, factories
import pytest

MODEL_LIST = [
    models.Game,
    models.Question,
    models.Selection,
]

FACTORY_LIST = [
    factories.game_factory,
    factories.question_factory,
    factories.selection_factory,
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "Model, Factory",
    zip(MODEL_LIST, FACTORY_LIST),
)
def test_admin_changelist_view_returns_200(Model, Factory, admin_client):
    Factory()
    model_name = Model._meta.model_name
    app_label = Model._meta.app_label
    url = reverse(f"admin:{app_label}_{model_name}_changelist")
    response = admin_client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "Model, Factory",
    zip(MODEL_LIST, FACTORY_LIST),
)
def test_search_admin_changelist_view_returns_200(Model, Factory, admin_client):
    Factory()
    model_name = Model._meta.model_name
    app_label = Model._meta.app_label
    url = reverse(f"admin:{app_label}_{model_name}_changelist")
    response = admin_client.get(url + "?q=search")
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.parametrize(
    "Model, Factory",
    zip(MODEL_LIST, FACTORY_LIST),
)
def test_admin_add_view_returns_200(Model, Factory, admin_client):
    Factory()
    model_name = Model._meta.model_name
    app_label = Model._meta.app_label
    url = reverse(f"admin:{app_label}_{model_name}_add")
    response = admin_client.get(url)
    assert response.status_code == 200
