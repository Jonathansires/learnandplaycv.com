"""Employee management with persistent SQLite storage and server-side admin sessions."""
from contextlib import contextmanager
import hashlib
import hmac
import io
import os
from pathlib import Path
import secrets
import sqlite3
import time
import warnings

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from PIL import Image, ImageOps, UnidentifiedImageError

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
router = APIRouter()
COOKIE = "lp_admin_session"
SESSION_SECONDS = 8 * 60 * 60
MAX_PHOTO_BYTES = 50 * 1024 * 1024
WEB_PHOTO_BYTES = 450 * 1024
Image.MAX_IMAGE_PIXELS = 60_000_000


@contextmanager
def database():
    path = Path(os.getenv("EMPLOYEE_DATABASE", str(BASE_DIR / "data" / "employees.sqlite3")))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, title TEXT NOT NULL DEFAULT '',
            sort_order INTEGER NOT NULL DEFAULT 0, photo BLOB, photo_version TEXT
        );
        CREATE TABLE IF NOT EXISTS gallery_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, description TEXT NOT NULL DEFAULT '',
            photo BLOB NOT NULL, photo_version TEXT NOT NULL, sort_order INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS admin_sessions (
            token_hash TEXT PRIMARY KEY, csrf TEXT NOT NULL,
            authenticated INTEGER NOT NULL DEFAULT 0, expires INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS login_attempts (client TEXT NOT NULL, attempted INTEGER NOT NULL);
        CREATE INDEX IF NOT EXISTS login_attempt_client ON login_attempts(client, attempted);
    """)
    try:
        with db:
            yield db
    finally:
        db.close()


def employees():
    with database() as db:
        return db.execute("SELECT id, name, title, sort_order, photo_version FROM employees ORDER BY sort_order, id").fetchall()


def get_employee(employee_id):
    with database() as db:
        employee = db.execute("SELECT id, name, title, sort_order, photo_version FROM employees WHERE id = ?", (employee_id,)).fetchone()
    if employee is None:
        raise HTTPException(404, "Employee not found")
    return employee


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def session(request):
    token = request.cookies.get(COOKIE, "")
    if not token or len(token) > 128:
        return None
    with database() as db:
        return db.execute("SELECT * FROM admin_sessions WHERE token_hash = ? AND expires > ?", (token_hash(token), int(time.time()))).fetchone()


def new_session(authenticated=False):
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    now = int(time.time())
    with database() as db:
        db.execute("DELETE FROM admin_sessions WHERE expires <= ?", (now,))
        db.execute("INSERT INTO admin_sessions VALUES (?, ?, ?, ?)", (token_hash(token), csrf, int(authenticated), now + SESSION_SECONDS))
    return token, csrf


def set_cookie(response, token):
    response.set_cookie(COOKIE, token, httponly=True, secure=os.getenv("ADMIN_COOKIE_SECURE", "true").lower() == "true", samesite="strict", max_age=SESSION_SECONDS, path="/admin")


def check_csrf(request, csrf, require_admin=True):
    current = session(request)
    if current is None or (require_admin and not current["authenticated"]):
        raise HTTPException(403, "Your session expired. Sign in again.")
    if not hmac.compare_digest(current["csrf"].encode(), csrf.encode()):
        raise HTTPException(403, "Invalid form token. Reload the page and try again.")
    return current


def render(request, template, **context):
    response = templates.TemplateResponse(template, {"request": request, **context})
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


def redirect(path="/admin/employees"):
    return RedirectResponse(path, status_code=303)


def password_hash(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def admin_configured():
    return bool(os.getenv("ADMIN_PASSWORD") or os.getenv("ADMIN_PASSWORD_HASH"))


def password_matches(password):
    if len(password) > 1024:
        return False
    configured_password = os.getenv("ADMIN_PASSWORD", "")
    if configured_password:
        return hmac.compare_digest(password.encode(), configured_password.encode())
    stored = os.getenv("ADMIN_PASSWORD_HASH", "")
    try:
        algorithm, salt, digest = stored.split("$")
        if algorithm != "pbkdf2_sha256" or len(password) > 1024:
            return False
        return hmac.compare_digest(stored, password_hash(password, salt))
    except (ValueError, TypeError):
        return False


@router.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request):
    return redirect()


@router.get("/admin/login", response_class=HTMLResponse)
async def login_page(request: Request):
    current = session(request)
    if current and current["authenticated"]:
        return redirect()
    token, csrf = new_session()
    response = render(request, "admin_login.html", csrf=csrf, configured=admin_configured())
    set_cookie(response, token)
    return response


@router.post("/admin/login")
async def login(request: Request, username: str = Form(""), password: str = Form(""), csrf: str = Form("")):
    check_csrf(request, csrf, require_admin=False)
    if not admin_configured():
        return render(request, "admin_login.html", csrf=csrf, configured=False)
    client = request.client.host if request.client else "unknown"
    now = int(time.time())
    with database() as db:
        db.execute("DELETE FROM login_attempts WHERE attempted < ?", (now - 900,))
        attempts = db.execute("SELECT COUNT(*) FROM login_attempts WHERE client = ?", (client,)).fetchone()[0]
        if attempts >= 10:
            response = render(request, "admin_login.html", csrf=csrf, configured=True, error="Too many sign-in attempts. Please try again in 15 minutes.")
            response.status_code = 429
            return response
        db.execute("INSERT INTO login_attempts VALUES (?, ?)", (client, now))
    valid_password = password_matches(password)
    if not hmac.compare_digest(username.encode(), os.getenv("ADMIN_USERNAME", "admin").encode()) or not valid_password:
        response = render(request, "admin_login.html", csrf=csrf, configured=True, error="The username or password is incorrect.")
        response.status_code = 401
        return response
    with database() as db:
        db.execute("DELETE FROM admin_sessions WHERE token_hash = ?", (token_hash(request.cookies.get(COOKIE, "")),))
        db.execute("DELETE FROM login_attempts WHERE client = ?", (client,))
    token, _ = new_session(authenticated=True)
    response = redirect()
    set_cookie(response, token)
    return response


@router.post("/admin/logout")
async def logout(request: Request, csrf: str = Form("")):
    current = check_csrf(request, csrf)
    with database() as db:
        db.execute("DELETE FROM admin_sessions WHERE token_hash = ?", (current["token_hash"],))
    response = redirect("/admin/login")
    response.delete_cookie(COOKIE, path="/admin")
    return response


@router.get("/admin/employees", response_class=HTMLResponse)
async def dashboard(request: Request):
    current = session(request)
    if not current or not current["authenticated"]:
        return redirect("/admin/login")
    notices = {"saved": "Employee saved. The team page is up to date.", "deleted": "Employee removed from the team page."}
    return render(request, "admin_employees.html", employees=employees(), csrf=current["csrf"], notice=notices.get(request.query_params.get("notice")))


@router.get("/admin/employees/new", response_class=HTMLResponse)
@router.get("/admin/employees/{employee_id:int}/edit", response_class=HTMLResponse)
async def employee_form(request: Request, employee_id: int = None):
    current = session(request)
    if not current or not current["authenticated"]:
        return redirect("/admin/login")
    employee = get_employee(employee_id) if employee_id else {"name": "", "title": "", "sort_order": 0}
    return render(request, "admin_employee_form.html", employee=employee, csrf=current["csrf"])


async def read_photo(photo):
    if not photo or not photo.filename:
        return None
    content = await photo.read(MAX_PHOTO_BYTES + 1)
    if len(content) > MAX_PHOTO_BYTES:
        raise ValueError("Choose a photo smaller than 50 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Choose a JPG, PNG, or WebP photo.")
                image.load()
                image = ImageOps.exif_transpose(image)
                image.thumbnail((1200, 1200))
                # Flatten transparency onto white and strip metadata by re-encoding.
                rgba = image.convert("RGBA")
                clean = Image.new("RGB", rgba.size, "white")
                clean.paste(rgba, mask=rgba.getchannel("A"))
                for edge in (1200, 1000, 800, 640):
                    clean.thumbnail((edge, edge), Image.Resampling.LANCZOS)
                    for quality in (85, 75, 65):
                        output = io.BytesIO()
                        clean.save(output, format="JPEG", quality=quality, optimize=True)
                        if output.tell() <= WEB_PHOTO_BYTES:
                            return output.getvalue()
                raise ValueError("This photo could not be prepared. Please try a different photo.")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValueError("That photo could not be opened. Choose a valid JPG, PNG, or WebP photo under 60 megapixels.") from exc


@router.post("/admin/employees/new")
@router.post("/admin/employees/{employee_id:int}/edit")
async def save_employee(request: Request, employee_id: int = None, csrf: str = Form(""), name: str = Form(""), title: str = Form(""), sort_order: str = Form("0"), photo: UploadFile = File(None), remove_photo: bool = Form(False)):
    current = check_csrf(request, csrf)
    existing = get_employee(employee_id) if employee_id else None
    values = {"id": employee_id, "name": name.strip(), "title": title.strip(), "sort_order": sort_order, "photo_version": existing["photo_version"] if existing else None}
    try:
        if not values["name"] or len(values["name"]) > 100:
            raise ValueError("Enter an employee name with 1–100 characters.")
        if len(values["title"]) > 120:
            raise ValueError("Keep the title to 120 characters or fewer.")
        try:
            order = int(sort_order)
            if not 0 <= order <= 9999:
                raise ValueError()
        except ValueError:
            raise ValueError("Display order must be a whole number from 0 to 9999.")
        image = await read_photo(photo)
    except ValueError as exc:
        response = render(request, "admin_employee_form.html", employee=values, csrf=current["csrf"], error=str(exc))
        response.status_code = 400
        return response
    with database() as db:
        if employee_id:
            db.execute("UPDATE employees SET name = ?, title = ?, sort_order = ? WHERE id = ?", (values["name"], values["title"], order, employee_id))
        else:
            employee_id = db.execute("INSERT INTO employees (name, title, sort_order) VALUES (?, ?, ?)", (values["name"], values["title"], order)).lastrowid
        if image is not None or remove_photo:
            db.execute("UPDATE employees SET photo = ?, photo_version = ? WHERE id = ?", (image, secrets.token_hex(8) if image else None, employee_id))
    return redirect("/admin/employees?notice=saved")


@router.post("/admin/employees/{employee_id:int}/delete")
async def delete_employee(request: Request, employee_id: int, csrf: str = Form("")):
    check_csrf(request, csrf)
    get_employee(employee_id)
    with database() as db:
        db.execute("DELETE FROM employees WHERE id = ?", (employee_id,))
    return redirect("/admin/employees?notice=deleted")


@router.get("/team/photos/{employee_id:int}")
async def employee_photo(employee_id: int):
    with database() as db:
        row = db.execute("SELECT photo FROM employees WHERE id = ?", (employee_id,)).fetchone()
    if row is None or row["photo"] is None:
        raise HTTPException(404, "Photo not found")
    return Response(bytes(row["photo"]), media_type="image/jpeg", headers={"Cache-Control": "no-cache", "X-Content-Type-Options": "nosniff"})


if __name__ == "__main__":
    import getpass
    password = getpass.getpass("New admin password (at least 12 characters): ")
    if len(password) < 12:
        raise SystemExit("Use at least 12 characters.")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match.")
    print("Add this line to .env (keep the single quotes):")
    print(f"ADMIN_PASSWORD_HASH='{password_hash(password)}'")
