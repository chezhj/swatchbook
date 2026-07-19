from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.CollectionView.as_view(), name="collection"),
    # Underscored names throughout: the DRF router owns the hyphenated ones.
    path("polish/new/", views.PolishCreateView.as_view(), name="polish_create"),
    path("polish/<int:pk>/", views.PolishDetailView.as_view(), name="polish_detail"),
    path("polish/<int:pk>/edit/", views.PolishUpdateView.as_view(), name="polish_update"),
    path("polish/<int:pk>/delete/", views.PolishDeleteView.as_view(), name="polish_delete"),
    path("compare/", views.ComparePickerView.as_view(), name="compare_picker"),
    path("compare/result/", views.CompareResultView.as_view(), name="compare_result"),
    path("log/", views.LogListView.as_view(), name="log_list"),
    path("log/new/", views.LogEntryCreateView.as_view(), name="log_create"),
    path("log/<int:pk>/", views.LogEntryDetailView.as_view(), name="log_detail"),
    path("log/<int:pk>/edit/", views.LogEntryUpdateView.as_view(), name="log_update"),
    path("log/<int:pk>/delete/", views.LogEntryDeleteView.as_view(), name="log_delete"),
    path("random/", views.RandomizerView.as_view(), name="randomizer"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
