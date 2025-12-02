# Cloud Deployment Guide - Free Tier Options

This guide covers multiple free cloud deployment options for the School Intelligence & Performance Management System.

## Quick Comparison

| Platform | Database | Storage | Limitations | Best For |
|----------|----------|---------|-------------|----------|
| **Render** | PostgreSQL (90 days) | Persistent | Sleeps after 15min inactivity | Production-ready apps |
| **Railway** | PostgreSQL | 1GB | $5 credit/month | Quick deployments |
| **PythonAnywhere** | MySQL/PostgreSQL | 512MB | Limited CPU | Simple hosting |
| **Fly.io** | PostgreSQL | 3GB | 3 shared VMs | Global deployment |

---

## Option 1: Render (Recommended)

**Pros:** Easy setup, automatic deployments, free PostgreSQL, custom domains
**Cons:** Spins down after 15 minutes of inactivity (50-second cold start)

### Prerequisites
1. GitHub account
2. Push your code to GitHub repository

### Step 1: Prepare Your Application

Create `render.yaml` in project root:

```yaml
databases:
  - name: students_performance_db
    databaseName: students_performance
    user: students_performance_user

services:
  - type: web
    name: students-performance-system
    env: python
    buildCommand: "./build.sh"
    startCommand: "gunicorn students_performance.wsgi:application"
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        fromDatabase:
          name: students_performance_db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: DJANGO_SETTINGS_MODULE
        value: students_performance.settings
```

### Step 2: Create Build Script

Create `build.sh` in project root:

```bash
#!/usr/bin/env bash
# exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
```

Make it executable:
```bash
chmod +x build.sh
```

### Step 3: Update Settings

Create `students_performance/production_settings.py`:

```python
from .settings import *
import dj_database_url

DEBUG = False
ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']

# Database
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://localhost/students_performance',
        conn_max_age=600
    )
}

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### Step 4: Update Requirements

Add to `requirements.txt`:
```
gunicorn==21.2.0
dj-database-url==2.1.0
psycopg2-binary==2.9.9
whitenoise==6.6.0
```

### Step 5: Update WSGI

Edit `students_performance/wsgi.py`:

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'students_performance.production_settings')

application = get_wsgi_application()
```

### Step 6: Deploy on Render

1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will detect `render.yaml` and create services
5. Click "Apply" to deploy

**First-time setup:**
```bash
# After deployment, create superuser via Render Shell
python manage.py createsuperuser
```

---

## Option 2: Railway

**Pros:** Very simple, automatic HTTPS, good free tier
**Cons:** $5 credit per month (usually enough for small apps)

### Step 1: Prepare Application

Create `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python manage.py migrate && gunicorn students_performance.wsgi",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Create `Procfile`:
```
web: gunicorn students_performance.wsgi --log-file -
release: python manage.py migrate
```

### Step 2: Deploy

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add PostgreSQL database from "New" → "Database" → "PostgreSQL"
6. Add environment variables:
   - `DJANGO_SETTINGS_MODULE=students_performance.production_settings`
   - `SECRET_KEY=<generate-random-string>`
   - Railway auto-provides `DATABASE_URL`

---

## Option 3: PythonAnywhere

**Pros:** Django-specific, easy for beginners, persistent
**Cons:** Limited resources, manual deployment

### Step 1: Sign Up

1. Go to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Create free account

### Step 2: Upload Code

```bash
# In PythonAnywhere Bash console
git clone https://github.com/yourusername/students_performance.git
cd students_performance
mkvirtualenv --python=/usr/bin/python3.10 myenv
pip install -r requirements.txt
```

### Step 3: Configure Web App

1. Go to "Web" tab → "Add a new web app"
2. Choose "Manual configuration" → Python 3.10
3. Set source code directory: `/home/yourusername/students_performance`
4. Set working directory: `/home/yourusername/students_performance`
5. Edit WSGI file (click link on Web tab):

```python
import os
import sys

path = '/home/yourusername/students_performance'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'students_performance.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### Step 4: Setup Database & Static Files

```bash
python manage.py migrate
python manage.py collectstatic
python manage.py createsuperuser
```

In Web tab, set static files:
- URL: `/static/`
- Directory: `/home/yourusername/students_performance/staticfiles/`

---

## Option 4: Fly.io

**Pros:** Good free tier, global deployment, persistent
**Cons:** Requires CLI installation

### Step 1: Install Fly CLI

```bash
# macOS
brew install flyctl

# Login
flyctl auth login
```

### Step 2: Initialize

```bash
cd /Users/ottiguntajyothinaidu/PycharmProjects/PythonProject3/students_performance
flyctl launch
```

This creates `fly.toml`:

```toml
app = "students-performance-system"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8000"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[statics]]
  guest_path = "/app/staticfiles"
  url_prefix = "/static/"
```

### Step 3: Add PostgreSQL

```bash
flyctl postgres create
flyctl postgres attach <postgres-app-name>
```

### Step 4: Deploy

```bash
flyctl deploy
```

---

## Environment Variables Setup

For all platforms, set these environment variables:

```bash
SECRET_KEY=<generate-with-django-secret-key-generator>
DEBUG=False
ALLOWED_HOSTS=.yourdomain.com,.onrender.com
DATABASE_URL=<auto-provided-by-platform>
```

Generate SECRET_KEY:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

---

## Post-Deployment Checklist

- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Collect static files: `python manage.py collectstatic`
- [ ] Test all dashboards (Student, Teacher, Management)
- [ ] Test API endpoints with authentication
- [ ] Verify PDF exports work
- [ ] Check topic mastery heatmap
- [ ] Test study plan generation
- [ ] Set up custom domain (optional)
- [ ] Configure email backend for notifications
- [ ] Set up monitoring/logging

---

## Troubleshooting

### Static Files Not Loading
```python
# Ensure in settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# In MIDDLEWARE, add after SecurityMiddleware:
'whitenoise.middleware.WhiteNoiseMiddleware',
```

### Database Connection Issues
```bash
# Check DATABASE_URL format
postgresql://user:password@host:port/database

# Test connection
python manage.py dbshell
```

### Application Crashes
```bash
# Check logs
# Render: Dashboard → Logs
# Railway: Dashboard → Deployments → View Logs
# Fly.io: flyctl logs
```

---

## Cost Optimization Tips

1. **Use SQLite for development**, PostgreSQL for production
2. **Optimize images** before uploading (compress, resize)
3. **Use CDN** for static files (Cloudflare free tier)
4. **Implement caching** (Redis free tier on Render/Railway)
5. **Monitor usage** to stay within free limits

---

## Recommended: Render Deployment

For this project, **Render** is recommended because:
- ✅ Free PostgreSQL database (90 days, then $7/month)
- ✅ Automatic deployments from GitHub
- ✅ Easy environment variable management
- ✅ Good documentation and support
- ✅ Custom domains with SSL
- ✅ Suitable for production use

---

## Next Steps

1. Choose a platform based on your needs
2. Follow the specific deployment steps above
3. Test thoroughly after deployment
4. Set up monitoring and backups
5. Consider upgrading to paid tier for production use

For detailed platform-specific issues, refer to:
- [Render Docs](https://render.com/docs)
- [Railway Docs](https://docs.railway.app)
- [PythonAnywhere Help](https://help.pythonanywhere.com)
- [Fly.io Docs](https://fly.io/docs)
