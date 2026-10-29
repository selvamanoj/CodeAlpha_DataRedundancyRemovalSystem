import hmac
import os
import re
from functools import wraps

import psycopg
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect
from psycopg.rows import dict_row
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
app.config["DATABASE_URL"] = os.getenv("DATABASE_URL", "")
app.config["ADMIN_PASSWORD"] = os.getenv("ADMIN_PASSWORD", "")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
CSRFProtect(app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(email):
    return (email or "").strip().lower()


def normalize_text(value):
    return " ".join((value or "").strip().split())


def validate_record(name, email, department):
    name, email, department = normalize_text(name), normalize_email(email), normalize_text(department)
    if not name or len(name) > 100:
        return "Name is required and must be 100 characters or fewer."
    if not email or len(email) > 254 or not EMAIL_RE.match(email):
        return "Enter a valid email address."
    if not department or len(department) > 100:
        return "Department is required and must be 100 characters or fewer."
    return None


def get_connection():
    database_url = app.config["DATABASE_URL"]
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured. Add it to your .env file.")
    return psycopg.connect(database_url, connect_timeout=10, row_factory=dict_row)


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS student_records (
                id BIGSERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(254) NOT NULL,
                email_normalized VARCHAR(254) NOT NULL UNIQUE,
                department VARCHAR(100) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_student_records_name
            ON student_records (LOWER(name))
        """)


_db_ready = False


@app.before_request
def ensure_database_ready():
    global _db_ready
    if request.endpoint == "static":
        return
    if not _db_ready and app.config["DATABASE_URL"]:
        init_db()
        _db_ready = True


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.get("/health")
def health():
    return {"status": "ok", "service": "data-redundancy-removal"}, 200


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("index"))
    if request.method == "POST":
        password = request.form.get("password", "")
        configured = app.config["ADMIN_PASSWORD"]
        if not configured:
            flash("Admin login is not configured. Set ADMIN_PASSWORD in environment variables.", "error")
        elif hmac.compare_digest(password, configured):
            session.clear()
            session["logged_in"] = True
            next_url = request.args.get("next", "")
            if not next_url.startswith("/") or next_url.startswith("//"):
                next_url = url_for("index")
            return redirect(next_url)
        else:
            flash("Incorrect password. Please try again.", "error")
    return render_template("login.html")


@app.post("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.get("/")
@login_required
def index():
    search = normalize_text(request.args.get("q", ""))[:100]
    with get_connection() as conn:
        if search:
            pattern = f"%{search}%"
            records = conn.execute("""
                SELECT id, name, email, department, created_at
                FROM student_records
                WHERE name ILIKE %s OR email ILIKE %s OR department ILIKE %s
                ORDER BY created_at DESC, id DESC LIMIT 250
            """, (pattern, pattern, pattern,)).fetchall()
        else:
            records = conn.execute("""
                SELECT id, name, email, department, created_at
                FROM student_records
                ORDER BY created_at DESC, id DESC LIMIT 250
            """).fetchall()
        total = conn.execute("SELECT COUNT(*) AS count FROM student_records").fetchone()["count"]
    return render_template("index.html", records=records, total=total, search=search)


@app.post("/records")
@login_required
def add_record():
    name = normalize_text(request.form.get("name", ""))
    email = normalize_email(request.form.get("email", ""))
    department = normalize_text(request.form.get("department", ""))
    error = validate_record(name, email, department)
    if error:
        flash(error, "error")
        return redirect(url_for("index"))

    with get_connection() as conn:
        duplicate = conn.execute(
            "SELECT id FROM student_records WHERE email_normalized = %s", (email,)
        ).fetchone()
        if duplicate:
            flash("REDUNDANT DATA: This email already exists. No record was added.", "error")
            return redirect(url_for("index"))

        possible_match = conn.execute("""
            SELECT id FROM student_records
            WHERE LOWER(name) = LOWER(%s) AND LOWER(department) = LOWER(%s)
            LIMIT 1
        """, (name, department)).fetchone()

        # The UNIQUE database constraint is the final protection against duplicate email entries.
        conn.execute("""
            INSERT INTO student_records (name, email, email_normalized, department)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email_normalized) DO NOTHING
        """, (name, email, email, department))

        saved = conn.execute(
            "SELECT id FROM student_records WHERE email_normalized = %s", (email,)
        ).fetchone()

    if not saved:
        flash("REDUNDANT DATA: This email already exists. No record was added.", "error")
    elif possible_match:
        flash("POSSIBLE MATCH: Name and department match, but the email differs. The record was saved to avoid a false positive.", "warning")
    else:
        flash("UNIQUE VERIFIED DATA: Record saved successfully.", "success")
    return redirect(url_for("index"))


@app.post("/records/<int:record_id>/delete")
@login_required
def delete_record(record_id):
    with get_connection() as conn:
        deleted = conn.execute(
            "DELETE FROM student_records WHERE id = %s RETURNING id", (record_id,)
        ).fetchone()
    flash("Record deleted." if deleted else "Record was not found.",
          "success" if deleted else "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
