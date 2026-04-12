# 🚀 Pre-Deployment Checklist

## ✅ Completed Tasks

### Tier 1: Critical Security (All Done ✓)
- [x] **Secrets to Environment Variables**
  - SECRET_KEY → os.getenv()
  - Database credentials → os.getenv()
  - Email credentials → os.getenv()
  
- [x] **DEBUG Mode Configuration**
  - DEBUG = False by default
  - Can be overridden via DEBUG env var
  
- [x] **ALLOWED_HOSTS Configuration**
  - From environment variables
  - Prevents Host header injection
  
- [x] **Email Domain Configuration**
  - SITE_DOMAIN uses environment variable
  - Email links will use production domain

### Tier 2: Production Setup (All Done ✓)
- [x] **HTTPS Enforcement**
  - SECURE_SSL_REDIRECT configured
  - SESSION_COOKIE_SECURE configured
  - CSRF_COOKIE_SECURE configured
  - Security headers (CSP, XSS filter) added
  - HSTS configured for production
  
- [x] **Production WSGI Server**
  - Gunicorn configured in Procfile
  - 2 workers for concurrency
  - Auto-runs migrations on deploy
  
- [x] **Static Files**
  - STATIC_ROOT configured
  - collectstatic ready to use
  
- [x] **Media Files**
  - MEDIA_ROOT already correct
  - Configure nginx to serve in production
  
- [x] **Database Connection Pooling**
  - CONN_MAX_AGE = 600
  - Reuses connections efficiently

### Files Created/Modified:
- [x] `.env.example` - Template with all variables
- [x] `Procfile` - Railway deployment config
- [x] `runtime.txt` - Python version spec
- [x] `requirements.txt` - Added gunicorn, python-dotenv, whitenoise
- [x] `LOCALKAAM/settings.py` - Updated with env variables
- [x] `DEPLOYMENT_GUIDE.md` - Step-by-step Railway guide
- [x] `DEPLOYMENT_CHANGES_SUMMARY.md` - What was changed

---

## 🔄 Next Steps (Ready to Deploy)

### Step 1: Verify Locally First
```bash
# In your project root:
cp .env.example .env

# Edit .env with LOCAL values:
# DEBUG=True
# DB_HOST=localhost
# etc.

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Test Locally:**
- Register a user ✓
- Check email (verify account) ✓
- Login ✓
- Create a job ✓

### Step 2: Push to GitHub
```bash
git add .
git commit -m "Add production deployment configuration (Tier 1 & 2)"
git push origin main
```

**Important:** Verify .env is NOT in git (it's in .gitignore)

### Step 3: Set Up Railway
1. Go to railway.app
2. Sign up with GitHub
3. Create new project
4. Connect LOCALKAAM repository
5. Add MySQL database plugin
6. Set environment variables (copy from .env.example)
7. Deploy

### Step 4: Configure Variables on Railway
Copy from `.env.example` and fill with production values:
```
SECRET_KEY=generate-a-long-random-key
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app,localhost
DB_NAME=railway
DB_USER=root
DB_PASSWORD=[from Railway MySQL]
DB_HOST=[from Railway MySQL]
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
SITE_DOMAIN=https://your-app.railway.app
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

### Step 5: Test After Deployment
- [ ] Visit Railway URL (should load)
- [ ] Register new account (should get email)
- [ ] Verify email works
- [ ] Login and access dashboard
- [ ] Create a job as customer
- [ ] Submit quotation as worker
- [ ] Start negotiation and send messages

---

## ⚠️ Critical Reminders

### SECURITY:
- ❌ NEVER commit `.env` file
- ❌ NEVER share SECRET_KEY or passwords
- ❌ NEVER use personal Gmail password (use app-specific password)
- ✅ ALWAYS use environment variables
- ✅ ALWAYS regenerate SECRET_KEY for production
- ✅ ALWAYS verify ALLOWED_HOSTS

### EMAIL SETUP (DO THIS FIRST):
1. Go to myaccount.google.com
2. Confirm 2-Step Verification is enabled
3. Search for "App password"
4. Select Mail → Your OS
5. Generate password
6. Copy to `EMAIL_HOST_PASSWORD` in Railway

### FIRST DEPLOYMENT:
- May take 5-10 minutes
- Check build logs for errors
- If migrations fail, check database connection
- If email fails, verify Gmail app password

---

## 📊 What's Changed

| Component | Before | After |
|-----------|--------|-------|
| Secrets | Hardcoded ❌ | Environment vars ✅ |
| Debug | Always on ❌ | Configurable ✅ |
| Server | Dev only ❌ | Gunicorn ✅ |
| Static files | Django serves ❌ | collectstatic ✅ |
| HTTPS | Not enforced ❌ | Enforced ✅ |
| Database | No pooling ❌ | Pooling enabled ✅ |
| Sessions | No timeout ❌ | 1 hour timeout ✅ |

---

## 📝 Files Reference

**Read These:**
- `DEPLOYMENT_GUIDE.md` - Full step-by-step guide
- `DEPLOYMENT_CHANGES_SUMMARY.md` - What was changed and why

**Reference:**
- `.env.example` - All environment variables
- `Procfile` - How Railway starts your app
- `runtime.txt` - Python version

**Key Modified:**
- `LOCALKAAM/settings.py` - All configuration
- `requirements.txt` - Production dependencies

---

## 🆘 Troubleshooting

**Issue: "Secret key not provided"**
- Fix: Set SECRET_KEY in environment variables

**Issue: "Host is not allowed"**
- Fix: Add your Railway domain to ALLOWED_HOSTS

**Issue: "Email not sending"**
- Fix: Verify EMAIL_HOST_PASSWORD is app-specific password (not Gmail password)

**Issue: "Static files 404"**
- Fix: Run `python manage.py collectstatic --noinput` in Railway terminal

**Issue: "Database connection refused"**
- Fix: Verify DB_HOST, DB_USER, DB_PASSWORD are correct from Railway

---

## ✨ Ready to Deploy!

Your application is now production-ready for a mini-project MVP on Railway!

**Estimated Time to Live:** 30-45 minutes

Questions? Check DEPLOYMENT_GUIDE.md or see Railway docs at docs.railway.app

---

Last Updated: 2026-04-12
Status: ✅ ALL TIER 1 & 2 COMPLETE
