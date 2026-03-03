# LieLens SaaS (Django + Tailwind)

Production-oriented scaffold for an AI credibility intelligence SaaS.

## Architecture

- `core/`: central settings, URLs, middleware, Celery bootstrap
- `apps/accounts`: registration, JWT login, profile + plan state
- `apps/analysis`: submission APIs, async processing, report generation
- `apps/billing`: Stripe checkout + webhook, usage reset task
- `apps/dashboard`: premium dark-theme dashboard template
- `services/`: feature extraction, ML scoring, risk engine, suggestions, PDF

## Key flow implemented

1. User registers (`/api/v1/accounts/register/`)
2. User logs in via JWT (`/api/v1/accounts/token/`)
3. User submits text (`POST /api/v1/analysis/submissions/`)
4. Plan enforcement middleware checks monthly usage
5. Celery processes submission asynchronously
6. Feature extraction + ML probability + hybrid risk score computed
7. Suggestions and PDF report generated and stored under `media/reports/`
8. Dashboard renders usage + history (`/dashboard/`)
9. Soft AI Rewriter can transform completed submissions into professional wording

## Local setup (venv)

```powershell
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Run worker in another terminal:

```powershell
celery -A core worker -l info
celery -A core beat -l info
```

## Test suite

```powershell
python manage.py check
python manage.py test apps.accounts apps.analysis apps.dashboard
```

CI workflow is available at `.github/workflows/ci.yml` and runs:
- migration drift check
- Django system checks
- app test suites

## Docker setup

```powershell
copy .env.example .env
docker compose up --build
```

Then run migrations in the web container:

```powershell
docker compose exec web python manage.py migrate
```

## Production settings scaffold

Use `core.settings_production` for hardened defaults:

```powershell
$env:DJANGO_SETTINGS_MODULE="core.settings_production"
python manage.py check --deploy
```

Important production envs:
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_SECRET_KEY`
- `POSTGRES_*`
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- `REDIS_CACHE_URL`
- `SECURE_SSL_REDIRECT=1`

## Notes

- Stripe fields are fully wired but require real test keys and price IDs.
- Monthly reset logic exists as a Celery task (`reset_monthly_usage_task`) and should be scheduled with `django-celery-beat`.
- Frontend uses Tailwind CDN + Chart.js + GSAP for a polished dashboard baseline.
- Rewriter mode defaults to rule-based (`LIELENS_REWRITE_MODE=rule`) with optional LLM mode if OpenAI SDK/key are configured.
