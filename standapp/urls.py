"""
URL configuration for standapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

@csrf_exempt
def root_view(request):
    """Simple API status endpoint for root URL"""
    return JsonResponse({
        'message': 'StandApp API is running',
        'status': 'ok',
        'endpoints': {
            'admin': '/admin/',
            'api_schema': '/api/schema/',
            'api_docs_swagger': '/api/schema/swagger-ui/',
            'api_docs_redoc': '/api/schema/redoc/',
            'api_auth': '/api/auth/',
            'api_teams': '/api/teams/',
            'api_standups': '/api/standups/',
            'api_slack': '/api/slack/'
        }
    })

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    # API endpoints
    path('api/auth/', include('authentication.urls')),
    path('api/teams/', include('teams.urls')),
    path('api/standups/', include('standups.urls')),
    path('api/slack/', include('slack_integration.urls')),
    # API schema and documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
