# Learn & Play

FastAPI website with a public team page and a password-protected employee editor.

## Configure admin access on the existing server

The systemd service uses `/var/www/learnandplaycv/venv`, so use that existing environment:

```sh
cd /var/www/learnandplaycv
sudo venv/bin/python -m pip install -r requirements.txt
sudo nano /var/www/learnandplaycv/.env
```

Preserve existing email and reCAPTCHA settings. Add or update these lines with your chosen password:

```dotenv
ADMIN_USERNAME=admin
ADMIN_PASSWORD='your chosen password'
ADMIN_COOKIE_SECURE=true
```

Save the file, then restart:

```sh
sudo systemctl restart learnandplaycv.service
sudo systemctl status learnandplaycv.service --no-pager -l
```

Visit `https://learnandplaycv.com/admin` and sign in using that username and password. No password hash command is needed. Keep the real `.env` private. `ADMIN_PASSWORD` takes precedence over `ADMIN_PASSWORD_HASH`; existing hash-only configurations still work. No default password is supplied.

## Run locally

For a new local environment only:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Create `.env` from `.env.example` only if `.env` does not already exist. Set `ADMIN_USERNAME` and `ADMIN_PASSWORD`. For local HTTP development only, set `ADMIN_COOKIE_SECURE=false`, then run:

```sh
.venv/bin/python main.py
```

Visit `http://localhost:8000/team` for the public page and `http://localhost:8000/admin` to sign in. The existing home and careers pages continue to use the email and reCAPTCHA configuration in `.env`.

## Manage employees

1. Sign in and choose **Add employee**.
2. Enter a name, optionally add a title, and select a JPG, PNG, or WebP photo up to 5 MB. Photos must be under 25 megapixels. Uploads are decoded, resized to fit 1200 × 1200, and re-encoded as JPEG without metadata.
3. Set display order if needed. Lower numbers appear first; ties follow the order employees were added.
4. Choose **Save employee**. Changes appear immediately on `/team`.

Choose **Edit** to update an employee, replace their photo, or remove their photo. **Remove** deletes the employee and their photo, after a browser confirmation. Employees without photos display their initial. The original Mono team template supplies the page layout and card styling; employee cards come from the database. The team page starts empty because the template's sample people are not real employee records.

## Hosting and persistence

This change runs in the existing Python deployment. Install the updated requirements and restart the app after deploying the source changes. It does not migrate the website to a different hosting service.

- Serve the app over HTTPS and leave `ADMIN_COOKIE_SECURE=true` in production.
- Set `ADMIN_USERNAME` and `ADMIN_PASSWORD` in the host's environment or private `.env`. This is one shared admin login for the site; individual admin accounts and password reset emails are not included.
- Records, photos, sessions, and sign-in attempt limits live together in `data/employees.sqlite3` by default. The directory is ignored by Git. Set `EMPLOYEE_DATABASE` to an absolute path on a persistent, writable disk if the host replaces the application directory on deploy.
- Back up the database using SQLite's backup API or `sqlite3 ... '.backup ...'`. Preserve it across releases. This setup supports a single host with workers sharing the same database, not hosts with separate local disks.
- Admin sessions expire after eight hours. Forms use CSRF tokens; successful sign-in rotates the session. Sign-in is limited to ten attempts per client connection address every 15 minutes. Configure Uvicorn's trusted proxy settings for your host so client addresses are accurate. Do not trust forwarded headers from arbitrary clients.
- To change the password, update `ADMIN_PASSWORD` in the environment, restart the app, and clear existing sessions with `DELETE FROM admin_sessions;` in SQLite if they should be revoked immediately.
- Keep `.env` and database backups private. Do not place the database in `static/`.

## Checks

Run the isolated employee-management tests (no email is sent):

```sh
.venv/bin/python -m unittest discover -s tests -v
```

The old root `test.py` is an email-sending script and is not part of this test command.
