"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)


 
def health_check(request):
    """
    GET /api/health/
    Render uses this to verify the service is running.
    Returns 200 as long as Django is up.
    """
    return JsonResponse({'status': 'ok', 'service': 'astrogyan-api'})



urlpatterns = [
    
    path('admin/', admin.site.urls),
     # ── AstroGyan API ────────────────────────────────────────────────────────
    path('api/v1/', include('core.api.urls')),

    # ── Health check (required by Render) ─────────────────────────────────────
    path('api/health/', health_check, name='health-check'),
 
    # ── OpenAPI / Swagger ────────────────────────────────────────────────────
    path('api/schema/',  SpectacularAPIView.as_view(),    name='schema'),
    path('api/docs/',    SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/',   SpectacularRedocView.as_view(url_name='schema'),   name='redoc')
]
