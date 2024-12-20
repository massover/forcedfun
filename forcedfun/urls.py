from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.urls import path
from django.conf import settings

from . import views

urlpatterns = [
    path("", views.index_view, name="index"),
    path(
        "login/", LoginView.as_view(template_name="forcedfun/login.html"), name="login"
    ),
    path("register/", views.register_view, name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("health/", views.health_view, name="health"),
    path("admin/", admin.site.urls),
    path("game/<slug:slug>/", views.game_detail_view, name="game-detail"),
    path(
        "question/<int:question_pk>/selection/create/",
        views.SelectionCreateView.as_view(),
        name="selection-create",
    ),
    path("question/<int:pk>/", views.question_detail_view, name="question-detail"),
    path(
        "question/<int:pk>/score/",
        views.QuestionScoreView.as_view(),
        name="question-score",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
