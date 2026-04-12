# LOCALKAAM Deployment Guide - Railway

## Overview
This guide covers deploying LOCALKAAM to Railway.app for production. Railway is a beginner-friendly PaaS that handles DevOps complexity while allowing learning opportunities.

## Pre-Deployment Checklist

### What's Been Fixed
✅ **Tier 1 (Critical) - COMPLETED:**
- [x] Secrets moved to environment variables (no hardcoding)
- [x] DEBUG = False in production
- [x] ALLOWED_HOSTS configured via environment
- [x] Email domain uses environment variable

✅ **Tier 2 (Production) - COMPLETED:**
- [x] HTTPS enforcement settings added
- [x] Gunicorn configuration (Procfile)
- [x] Static files configured (STATIC_ROOT added)
- [x] Media files path configured
- [x] Database connection pooling enabled (CONN_MAX_AGE)
- [x] Security headers added (CSP, HSTS)
- [x] Session configuration

✅ **Files Created/Modified:**
- `LOCALKAAM/settings.py` - Updated with environment variables and security settings
- `.env.example` - Template for environment variables
- `requirements.txt` - Added production dependencies (gunicorn, python-dotenv, whitenoise)
- `Procfile` - Railway deployment configuration
- `runtime.txt` - Python version specification

---

## Step-by-Step Deployment to Railway

### Prerequisites
1. GitHub account
2. Railway account (free at railway.app)
3. Your code pushed to GitHub

### Step 1: Push Code to GitHub

```bash
cd LOCALKAAM
git add .
git commit -m "Production-ready deployment configuration"
git push origin main
```

**Important:** Make sure `.env` is NOT in git (it's in .gitignore)

### Step 2: Create Railway Account & Connect Repository

1. Go to https://railway.app
2. Sign up with GitHub
3. Create new project
4. Select "Deploy from GitHub repo"
5. Choose `LOCALKAAM` repository
6. Authorize Railway to access your repo

### Step 3: Add MySQL Database

1. In Railway dashboard, click "Add Service"
2. Select "MySQL"
3. Railway auto-generates:
   - Database name: `railway` (default)
   - Username: `root` (default)
   - Password: (auto-generated)
   - Host: (auto-assigned)

**Note:** Copy these credentials - you'll need them for environment variables

### Step 4: Configure Environment Variables

In Railway Dashboard, go to your project and add these environment variables:

```
# Django Settings
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app-name.railway.app,localhost,127.0.0.1

# Database (from Railway MySQL service)
DB_ENGINE=django.db.backends.mysql
DB_NAME=railway
DB_USER=root
DB_PASSWORD=[auto-generated-password-from-railway]
DB_HOST=[database-host-from-railway]
DB_PORT=3306

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=LocalKaam <noreply@localkaam.com>

# Site Configuration
SITE_DOMAIN=https://your-app-name.railway.app

# Security (for HTTPS in production)
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Step 5: Deploy

1. In Railway dashboard, click "Deploy"
2. Railway will:
   - Detect `Procfile`
   - Install dependencies from `requirements.txt`
   - Run migrations (from Procfile: `python manage.py migrate`)
   - Start Gunicorn web server

### Step 6: Verify Deployment

After deployment completes:

1. Check build logs for errors
2. Open your Railway app URL
3. Test these flows:
   - User registration (should send verification email)
   - Email verification (check inbox)
   - Login
   - Dashboard access
   - Create a job (customer)

---

## Email Setup (Gmail)

Your hardcoded Gmail credentials are now exposed. **DO THIS IMMEDIATELY:**

### Create Gmail App Password

1. Go to myaccount.google.com
2. Left sidebar → Security
3. Enable 2-Step Verification (if not already done)
4. Search for "App password"
5. Select Mail → Windows Computer (or your OS)
6. Generate app-specific password
7. Copy this password to Railway `EMAIL_HOST_PASSWORD`

**DO NOT use your actual Gmail password - use the app-specific password!**

---

## Troubleshooting

### Issue: "Host is not allowed" error
**Fix:** Add your Railway domain to `ALLOWED_HOSTS` in environment variables

### Issue: Static files not loading (CSS/styling broken)
**Fix:** Run in Railway terminal:
```bash
python manage.py collectstatic --noinput
```

### Issue: Email not sending
**Fix:** Verify these in Railway environment variables:
- `EMAIL_HOST_USER` is correct email
- `EMAIL_HOST_PASSWORD` is app-specific password (not regular password)
- `EMAIL_PORT` = 587

### Issue: Database connection refused
**Fix:** 
1. Verify `DB_HOST` is correct (Railway generates unique host)
2. Verify `DB_PASSWORD` is correct
3. Restart Railway service

### Issue: Migrations not running
**Check:** Railway build logs - scroll to see migration output

---

## Local Development After Deployment

### Setup Local .env File

Copy `.env.example` to `.env` and fill in local values:

```bash
cp .env.example .env
```

Edit `.env`:
```
DEBUG=True
SECRET_KEY=any-key-works-for-development
ALLOWED_HOSTS=localhost,127.0.0.1
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your-local-password
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
SITE_DOMAIN=http://localhost:8000
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
```

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

---

## Production Monitoring Checklist

After deployment, monitor these:

- [ ] Check Railway logs for errors
- [ ] Test user registration → email verification
- [ ] Test password reset flow
- [ ] Test job creation and quotation system
- [ ] Monitor Railway resource usage (CPU, memory)
- [ ] Check for slow queries (if more than 10 users)

---

## What's NOT Implemented Yet (Optional Future Improvements)

These can be added later when scaling:

- Real-time notifications (WebSockets) - works fine with manual refresh for MVP
- Error tracking (Sentry)
- Performance monitoring (Datadog)
- CDN for static files (Cloudflare)
- Database backups automation
- Log aggregation
- Load testing

---

## Important Security Reminders

⚠️ **NEVER:**
- Commit `.env` file to git
- Share `EMAIL_HOST_PASSWORD` or `SECRET_KEY` in chat/email
- Use same password as Gmail account
- Enable DEBUG in production

✅ **ALWAYS:**
- Rotate secrets regularly
- Use environment variables for all sensitive data
- Monitor Railway for unusual activity
- Keep dependencies updated

---

## Support & Documentation

- Railway Docs: https://docs.railway.app
- Django Deployment: https://docs.djangoproject.com/en/6.0/howto/deployment/
- Gunicorn: https://gunicorn.org/

---

## Cost Estimation

**Railway Free Tier:**
- $5 free credit/month
- For 1-10 users: Likely fits within free tier
- Estimate: $0-3/month with moderate usage

**Scaling:**
- If you exceed free tier, Railway charges pay-as-you-go (~$0.02-0.05/hour for web dyno)
- Database: ~$5/month for managed MySQL

---

Generated: 2026-04-12
Last Updated: Post-deployment configuration
