# Git Commit Guide

## What to Commit

Run these commands in your project root:

```bash
git add .
git commit -m "Production deployment configuration (Tier 1 & 2 hardening)

- Move all secrets to environment variables (SECRET_KEY, DB credentials, email)
- Configure DEBUG mode from environment (default: False)
- Set ALLOWED_HOSTS from environment variables
- Add HTTPS/SSL enforcement (SECURE_SSL_REDIRECT, secure cookies)
- Configure Gunicorn WSGI server with Procfile
- Setup static files for production (STATIC_ROOT, collectstatic)
- Enable database connection pooling (CONN_MAX_AGE)
- Add security headers (CSP, HSTS, XSS filter)
- Configure session timeouts and security
- Add production dependencies (gunicorn, python-dotenv, whitenoise)
- Create .env.example template for environment variables
- Add deployment guides and checklists

Ready for Railway deployment."

git push origin main
```

---

## What NOT to Commit

These should already be in .gitignore:

```
.env                    # ❌ Never commit - has secrets
.env.local              # ❌ Local overrides
db.sqlite3              # ❌ Local database
/media/                 # ❌ User uploads
/staticfiles/           # ❌ Collected static files
__pycache__/            # ❌ Python cache
.ruff_cache/            # ❌ Tool cache
```

---

## Verify Before Pushing

```bash
# Check what will be committed
git status

# Should show:
# - LOCALKAAM/settings.py (modified)
# - requirements.txt (modified)
# - .env.example (new)
# - Procfile (new)
# - runtime.txt (new)
# - DEPLOYMENT_GUIDE.md (new)
# - DEPLOYMENT_CHANGES_SUMMARY.md (new)
# - PRE_DEPLOYMENT_CHECKLIST.md (new)

# Check that .env is NOT listed
git status | grep .env  # Should return nothing
```

---

## After Commit

Push to GitHub:
```bash
git push origin main
```

Your repository is now ready for Railway deployment!

---

## Helpful Commands

**View commit before pushing:**
```bash
git log --oneline -1
```

**See what changed in settings.py:**
```bash
git diff LOCALKAAM/settings.py
```

**See all changes that will be committed:**
```bash
git diff --cached
```

---

Done! Ready to deploy! 🚀
