# Podsumowanie naprawy błędu 403 Forbidden

## Problem

Występował uporczywy błąd `403 Forbidden` przy żądaniach `POST` do endpointu `/api/v1/report_issue/`. Błąd pojawiał się tylko w środowisku produkcyjnym opartym na Dockerze (Nginx + Gunicorn + Django), a nie występował podczas pracy lokalnej, nawet z `DEBUG=False`.

## Analiza i diagnoza

Po wyeliminowaniu wielu standardowych przyczyn (CSRF, CORS, `ALLOWED_HOSTS`, konfiguracja proxy), ostateczna diagnoza była możliwa dzięki analizie nagłówków HTTP wysyłanych przez przeglądarkę.

**Główna przyczyna:**
Błąd był spowodowany przez domyślną klasę uwierzytelniania w Django REST Framework – `SessionAuthentication`. W połączeniu z żądaniem API, które używało `Content-Type: application/json`, ten mechanizm zawodził po cichu w środowisku produkcyjnym za proxy. `SessionAuthentication` jest przeznaczony głównie do tradycyjnych aplikacji webowych opartych na formularzach, a nie do bezstanowego API.

## Ostateczne rozwiązanie

Rozwiązaniem była zmiana domyślnego mechanizmu uwierzytelniania na `TokenAuthentication`, który jest standardem dla tego typu API.

### Wymagane zmiany w kodzie

1.  **W pliku `backend_project/settings.py`:**
    *   Dodano `'rest_framework.authtoken'` do listy `INSTALLED_APPS`.
    *   W słowniku `REST_FRAMEWORK`, zmieniono `DEFAULT_AUTHENTICATION_CLASSES` z `SessionAuthentication` na `TokenAuthentication`.

    ```python
    # backend_project/settings.py

    INSTALLED_APPS = [
        # ...
        'rest_framework',
        'corsheaders',
        'api_v1.apps.ApiV1Config',
        'rest_framework.authtoken', # DODANO
    ]

    # ...

    REST_FRAMEWORK = {
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.AllowAny',
        ],
        'DEFAULT_AUTHENTICATION_CLASSES': [
            # ZMIENIONO z SessionAuthentication
            'rest_framework.authentication.TokenAuthentication',
        ],
    }
    ```

### Wymagane kroki wdrożeniowe

1.  **Przebudowanie obrazu Docker:** Należało przebudować obraz, aby uwzględnić zmiany w kodzie.
    ```bash
    docker compose up -d --build --force-recreate
    ```
2.  **Uruchomienie migracji:** Po uruchomieniu nowego kontenera, konieczne było wykonanie migracji, aby Django stworzyło w bazie danych tabelę `authtoken_token` do przechowywania tokenów.
    ```bash
    docker compose exec web python manage.py migrate
    ```

### Rekomendowane, ale niekluczowe zmiany (dobre praktyki)

Podczas debugowania wprowadziliśmy kilka innych zmian, które, choć nie rozwiązały tego konkretnego problemu, są dobrymi praktykami w tego typu konfiguracji i warto je zachować:

*   **W `docker-compose.yml`:** Dodanie flagi `--forwarded-allow-ips="*"` do komendy Gunicorna, aby ufał nagłówkom z proxy.
*   **W `nginx/nginx.conf`:** Dodanie `proxy_set_header Origin http://$host;` do konfiguracji proxy.
*   **W `frontend/src/services/api.js`:** Dodanie logiki do obsługi i wysyłania tokenu CSRF.