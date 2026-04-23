# HealthSync

HealthSync is a Django REST API with JWT authentication, service-layer architecture, and PostgreSQL support (including Supabase via connection string).

## Project Structure

- `accounts` for authentication and user-related APIs
- `patients` for patient resources
- `doctors` for doctor resources
- `mappings` for patient-doctor assignment resources
- `config/settings/base.py` for shared settings
- `config/settings/dev.py` for development overrides

## Environment Setup

1. Create and fill your `.env` from `.env.example`.
2. Ensure PostgreSQL is running with the credentials in `.env`.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run checks:

```bash
python manage.py check
```

## API Endpoints

- `/api/auth/register/`
- `/api/auth/login/`
- `/api/auth/refresh/`
- `/api/patients/`
- `/api/patients/{id}/`
- `/api/doctors/`
- `/api/doctors/{id}/`
- `/api/patient-doctors/`

These endpoints are implemented and ready for manual/API client validation.

## UI Routes

- `/` (Login)
- `/ui/dashboard/`
- `/ui/patients/`
- `/ui/doctors/`
- `/ui/mappings/`

## Supabase Setup (Connection String)

1. In Supabase, open Project Settings -> Database.
2. Copy the PostgreSQL connection string (Direct or Pooler).
3. Put it in `.env`:

```env
DATABASE_URL=postgresql://postgres:your_password@your_host:5432/postgres?sslmode=require
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Apply migrations:

```bash
python manage.py migrate
```

6. Run server:

```bash
python manage.py runserver
```

## Expected Database Schema After Migration

- `accounts_user`
- `patients_patient`
- `doctors_doctor`
- `mappings_patientdoctormapping`

### Key Constraints

- `accounts_user.email` unique + indexed
- `patients_patient.created_by_id` foreign key to custom user
- `mappings_patientdoctormapping` unique pair constraint on `(patient_id, doctor_id)`

## Deployment

- Production settings module: `config.settings.prod`
- Procfile included for Gunicorn deployment.
- Detailed deployment guide: `DEPLOYMENT.md`