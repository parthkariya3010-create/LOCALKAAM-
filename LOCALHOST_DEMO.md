# LocalKaam - Localhost Demo Setup

This guide explains how to run LocalKaam on your local machine for demonstration purposes.

## Prerequisites

- Python 3.11+ installed
- MySQL Server running (or will use SQLite if not available)
- Git

## Quick Start

### 1. Clone/Navigate to Project

```bash
cd "C:\Users\parth\OneDrive\Desktop\Test Project\LOCALKAAM"
```

### 2. Create Virtual Environment (if needed)

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Start Development Server

```bash
python manage.py runserver
```

The application will be available at: **http://localhost:8000**

## Testing the Application

### Home Page
- Open http://localhost:8000 in your browser
- You should see the LocalKaam landing page

### User Registration
1. Click "Register" or navigate to http://localhost:8000/accounts/register/
2. Fill in the form:
   - Full Name: Test User
   - Email: testuser@example.com
   - Role: Customer or Worker
   - Location: Mumbai (or any location)
   - Password: TestPass123!
3. Click "Register"
4. You'll be redirected to login page

### User Login
1. Use the email and password you just registered with
2. You'll be logged in and redirected to dashboard

### Features to Test

#### For Customers:
- Dashboard: http://localhost:8000/accounts/customer/dashboard/
- Create Job: http://localhost:8000/accounts/customer/create-job/
- View Jobs Posted: Dashboard
- View Quotations: After creating a job and workers submit quotations

#### For Workers:
- Dashboard: http://localhost:8000/accounts/worker/dashboard/
- View Available Jobs: Browse jobs
- Submit Quotations: Apply for jobs
- View Profile: http://localhost:8000/accounts/profile/

### Email Verification Note

By default, email verification is enabled in development. To bypass this:

1. Go to Django admin: http://localhost:8000/admin/
2. Login with Django superuser credentials (create one with: `python manage.py createsuperuser`)
3. Navigate to Users and manually mark `is_email_verified = True`

Or disable email verification temporarily in `accounts/views.py` for demo purposes.

## Database

- Development uses MySQL (configured in settings.py)
- If MySQL is not available, the app falls back to SQLite
- All data is stored locally in your machine

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

## Troubleshooting

### Port 8000 Already in Use
```bash
python manage.py runserver 8001
# Then access http://localhost:8001
```

### Database Connection Errors
- Ensure MySQL is running (if using MySQL)
- Or simply use SQLite by not having MySQL running

### Missing Static Files
```bash
python manage.py collectstatic --noinput
```

### Clear Cookies/Sessions
Delete or clear browser cookies for localhost to reset user sessions.

## Project Structure

```
LOCALKAAM/
├── accounts/              # User accounts app
│   ├── models.py         # User, Job, Quotation models
│   ├── views.py          # View logic
│   ├── forms.py          # Form definitions
│   └── urls.py           # URL routing
├── templates/            # HTML templates
├── static/              # CSS, JavaScript, images
├── LOCALKAAM/           # Project settings
│   ├── settings.py      # Configuration
│   ├── urls.py          # Main URL routing
│   └── wsgi.py          # WSGI application
├── manage.py            # Django management command
└── requirements.txt     # Python dependencies
```

## Key Features Demonstrated

✅ User Registration & Authentication  
✅ Role-based Access (Customer/Worker)  
✅ Job Posting (Customers)  
✅ Quotation System (Workers)  
✅ User Profiles  
✅ Rate Limiting on Registration  
✅ CSRF Protection  
✅ Email Verification (optional)  

## Default Credentials for Testing

Use any unique email and password to register new accounts:

```
Email: any-email@example.com
Password: Any Strong Password (min 8 chars, mix of letters/numbers/symbols)
```

---

**Ready to demo!** Run `python manage.py runserver` and visit http://localhost:8000
