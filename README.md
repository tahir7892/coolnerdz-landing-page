# CoolNerdz

Django project serving the CoolNerdz "coming soon" landing page and the waitlist API.

## Stack

- Django 5.2 (templates + views)
- Django REST Framework (`/api/waitlist`)
- SQLite (`db.sqlite3`)

There is no Node.js component. The project runs entirely through `manage.py` / Gunicorn + Django.

## Local development

```bash
python3 -m venv env
env/bin/pip install -r requirements.txt
cp .env.example .env
env/bin/python manage.py migrate
env/bin/python manage.py runserver
```

Visit http://127.0.0.1:8000/.

## Tests

```bash
env/bin/python manage.py test
```

## Project layout

```text
manage.py
coolnerdz/           # settings, urls, wsgi/asgi
users/                # WaitlistEntry model, home page view, DRF API
templates/            # base.html, includes/, error pages
static/               # css/, js/
deploy/               # systemd unit for Gunicorn
nginx.coolnerdz.com.conf
.github/workflows/deploy.yml
```

## Deployment

Gunicorn runs as the `coolnerdz-django` systemd service (see
`deploy/coolnerdz-django.service`), fronted by Nginx
(`nginx.coolnerdz.com.conf`), which proxies all requests to Gunicorn on
`127.0.0.1:8000` and serves `/static/` and `/media/` directly.

The GitHub Actions workflow in `.github/workflows/deploy.yml` rsyncs the
repo to the server, installs Python dependencies into a venv, runs
migrations and `collectstatic`, then restarts the `coolnerdz-django`
service. It never overwrites the server's `db.sqlite3`.
