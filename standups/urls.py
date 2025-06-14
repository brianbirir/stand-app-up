from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'standups', views.StandupViewSet)
router.register(r'responses', views.StandupResponseViewSet)
router.register(r'metrics', views.StandupMetricsViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
]