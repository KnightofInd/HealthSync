# Deployment Guide

This project supports local development with config.settings.dev and production deployment with config.settings.prod.

## 1. Required Environment Variables

Set these on your deployment platform:

- DJANGO_SETTINGS_MODULE=config.settings.prod
- DJANGO_SECRET_KEY=<long-random-secret>
- DJANGO_DEBUG=False
- DJANGO_ALLOWED_HOSTS=<your-domain>,<platform-hostname>
- DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-domain>,https://<platform-hostname>
- DATABASE_URL=<supabase-postgres-connection-string>
- POSTGRES_CONN_MAX_AGE=600
- JWT_ACCESS_MINUTES=30
- JWT_REFRESH_DAYS=7

Optional security tuning:

- DJANGO_SECURE_SSL_REDIRECT=True
- DJANGO_SECURE_HSTS_SECONDS=31536000
- DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
- DJANGO_SECURE_HSTS_PRELOAD=True

## 2. Build and Release Commands

Install dependencies:

pip install -r requirements.txt

Apply migrations:

python manage.py migrate

Run deployment checks:

python manage.py check --deploy --settings=config.settings.prod

## 3. Start Command

Gunicorn command:

gunicorn config.wsgi:application --log-file -

A Procfile is included with this command.

## 4. Supabase Notes

- Use the Database connection string, not the API URL.
- Ensure the password is URL-encoded if it contains special characters.
- Keep sslmode=require in the connection string.

## 5. Verify After Deploy

- /api/auth/register/ responds with 201 on valid payload
- /api/auth/login/ returns access and refresh tokens
- Protected endpoints reject requests without Bearer token
