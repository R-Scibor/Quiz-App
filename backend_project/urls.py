"""
URL configuration for backend_project project.

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
from django.urls import path, include, re_path
from django.views.generic.base import RedirectView
from api_v1.views import ReactAppView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api/v1/', include('api_v1.urls')),
    
        # --- DODANA SEKCJA DLA BRAKUJĄCYCH OBRAZKÓW ---
    # Przekierowanie dla favicona i innych zasobów z katalogu /public
    path('icon.png', RedirectView.as_view(url='/static/icon.png', permanent=True)),
    # Dodaj tutaj kolejne linie, jeśli brakuje innych plików
    # --- KONIEC DODANEJ SEKCJI ---
    
    # Ta reguła musi być na końcu. Przechwytuje wszystkie inne ścieżki
    # i przekazuje je do aplikacji React.
    re_path(r'^.*$', ReactAppView.as_view(), name='react-app'),
]