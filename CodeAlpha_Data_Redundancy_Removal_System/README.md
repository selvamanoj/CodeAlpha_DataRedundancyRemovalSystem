# Cloud-Based Data Redundancy Removal System

A CodeAlpha Cloud Computing internship project using Python Flask and Supabase PostgreSQL. The application validates records, blocks duplicate email addresses, flags possible matches, and provides a searchable dashboard.

## Features
- Admin login using an environment-configured password.
- Add records with name, email, and department validation.
- Normalize email addresses by trimming whitespace and converting to lowercase.
- Reject duplicate emails; PostgreSQL also enforces a unique constraint.
- Flag same-name/same-department records with a different email as a possible match rather than automatically rejecting a legitimate record.
- Search, list, and delete records.
- Parameterized SQL, CSRF protection, and a `/health` endpoint.
- Responsive mobile-friendly dashboard.

## Stack
Python 3.12, Flask, Supabase PostgreSQL, Psycopg 3, HTML/CSS, Gunicorn.

## Run locally on Windows
Install Python 3.12+ and Git. Open PowerShell in this folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks virtual-environment activation, use `.\.venv\Scripts\python.exe` instead of `python`.

Edit `.env` and set the real `DATABASE_URL`, `SECRET_KEY`, and `ADMIN_PASSWORD`. Never upload `.env` to GitHub. Generate a secret key:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

## Configure Supabase
1. Create a Supabase project.
2. Open **Connect** and copy the **Session pooler** connection string for hosted apps.
3. Replace the password placeholder carefully; retain SSL mode if present.
4. The app creates the `student_records` table automatically. Or run `schema.sql` in Supabase SQL Editor.

The URI will resemble this example, but use the exact connection string from your Supabase project:

```text
postgresql://postgres.PROJECT_REF:DB_PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres?sslmode=require
```

If your database password includes URL-reserved characters, use a properly URL-encoded password or copy the dashboard-provided URI and replace the password carefully.

## Start
```powershell
python -m flask --app app run
```
Open `http://127.0.0.1:5000` and sign in using your `ADMIN_PASSWORD`.

## Tests
```powershell
python -m pytest -q
```
Manual checks:
1. Add `Asha Kumar`, `asha@example.com`, `AIDS` → saved.
2. Add the same email as `ASHA@example.com` → duplicate rejected.
3. Add `Asha Kumar`, `asha2@example.com`, `AIDS` → possible-match warning, record accepted.
4. Search records and delete a test record.
5. Open `/health` → JSON status.

## GitHub upload
Create an empty repository such as `CodeAlpha_DataRedundancyRemovalSystem`, then run in this folder:

```powershell
git init
git add .
git status
git commit -m "Build cloud data redundancy removal system"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/CodeAlpha_DataRedundancyRemovalSystem.git
git push -u origin main
```
Replace `YOUR-USERNAME`. Before committing, verify `.env` is not shown by `git status`.

## Deploy on Render
1. Push this folder to GitHub.
2. In Render choose **New + → Web Service** and connect the repository.
3. Configure:
   - Runtime: Python
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT --timeout 60`
4. In Render environment settings add:
   - `DATABASE_URL`: Supabase Session Pooler connection URI
   - `SECRET_KEY`: a long random secret
   - `ADMIN_PASSWORD`: a strong, unique password
   - `SESSION_COOKIE_SECURE`: `true`
5. Deploy, open the assigned Render URL, log in, test adding duplicates, and check `/health`.

Hosting plans and free-instance sleep limits may change; check Render's current plan details before depending on it for a deadline.

## Security reminders
Do not publish credentials in code, screenshots, videos, or GitHub. Use HTTPS, a unique password, and `SESSION_COOKIE_SECURE=true` for deployed HTTPS. This is a student demo; production use would need stronger access controls, rate limiting, auditing, backups, and a privacy policy.

## Suggested 60–90 second demo
1. Show the login screen.
2. Add a unique record and show success.
3. Try the same email with different capitalization and show duplicate rejection.
4. Add a similar name with a different email and explain the possible-match warning.
5. Search and delete a record.
6. Show the deployed site and GitHub repository.

## Resume title
**Cloud-Based Data Redundancy Removal System | Python, Flask, Supabase PostgreSQL**

Developed a cloud-connected web application to validate records, detect duplicate email entries, flag possible false positives, and maintain database integrity using PostgreSQL constraints and parameterized queries.
