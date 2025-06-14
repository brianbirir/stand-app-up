from django.urls import path
from . import views

urlpatterns = [
    path('interactions/', views.SlackInteractionsView.as_view(), name='slack_interactions'),
    path('events/', views.SlackEventsView.as_view(), name='slack_events'),
    path('commands/', views.SlackSlashCommandView.as_view(), name='slack_commands'),
]