# Learn & Play

FastAPI website with a public team page and a password-protected employee editor.

## Run locally

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/python employee_admin.py
```

The last command prompts for a password (at least 12 characters) and prints a salted password hash. Copy the full `ADMIN_PASSWORD_HASH='...'` line into `.env`, preserving the single quotes. Set `ADMIN_USERNAME` to your chosen login name. No default password is provided; sign-in stays disabled until a hash is configured.

For local HTTP development only, set `ADMIN_COOKIE_SECURE=false` in `.env`, then run:

```sh
.venv/bin/python main.py
```

Visit `http://localhost:8000/team` for the public page and `http://localhost:8000/admin` to sign in. The existing home and careers pages continue to use the email and reCAPTCHA configuration in `.env`.

## Manage employees

1. Sign in and choose **Add employee**.
2. Enter a name, optionally add a title, and select a JPG, PNG, or WebP photo up to 5 MB. Photos must be under 25 megapixels. Uploads are decoded, resized to fit 1200 × 1200, and re-encoded as JPEG without metadata.
3. Set display order if needed. Lower numbers appear first; ties follow the order employees were added.
4. Choose **Save employee**. Changes appear immediately on `/team`.

Choose **Edit** to update an employee, replace their photo, or remove their photo. **Remove** deletes the employee and their photo, after a browser confirmation. Employees without photos display their initial. The team page starts empty; the previous template's sample people are not real employee records.

## Hosting and persistence

This change runs in the existing Python deployment. Install the updated requirements and restart the app after deploying the source changes. It does not migrate the website to a different hosting service.

- Serve the app over HTTPS and leave `ADMIN_COOKIE_SECURE=true` in production.
- Set `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` in the host's environment or private `.env`. This is one shared admin login for the site; individual admin accounts and password reset emails are not included.
- Records, photos, sessions, and sign-in attempt limits live together in `data/employees.sqlite3` by default. The directory is ignored by Git. Set `EMPLOYEE_DATABASE` to an absolute path on a persistent, writable disk if the host replaces the application directory on deploy.
- Back up the database using SQLite's backup API or `sqlite3 ... '.backup ...'`. Preserve it across releases. This setup supports a single host with workers sharing the same database, not hosts with separate local disks.
- Admin sessions expire after eight hours. Forms use CSRF tokens; successful sign-in rotates the session. Sign-in is limited to ten attempts per client connection address every 15 minutes. Configure Uvicorn's trusted proxy settings for your host so client addresses are accurate. Do not trust forwarded headers from arbitrary clients.
- To change the password, generate a new hash, update the environment, restart the app, and clear existing sessions with `DELETE FROM admin_sessions;` in SQLite if they should be revoked immediately.
- Keep `.env` and database backups private. Do not place the database in `static/`.

## Checks

Run the isolated employee-management tests (no email is sent):

```sh
.venv/bin/python -m unittest discover -s tests -v
```

The old root `test.py` is an email-sending script and is not part of this test command.
