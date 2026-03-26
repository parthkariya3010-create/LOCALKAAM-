from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from functools import wraps
from django.http import JsonResponse
import time

class RateLimiter:
    def __init__(self):
        self._cache = {}
    
    def is_rate_limited(self, key, max_attempts, timeout):
        now = time.time()
        if key in self._cache:
            attempts, timestamps = self._cache[key]
            timestamps = [t for t in timestamps if now - t < timeout]
            if len(timestamps) >= max_attempts:
                remaining_time = int(timeout - (now - timestamps[0]))
                return True, remaining_time
            timestamps.append(now)
            self._cache[key] = (len(timestamps), timestamps)
        else:
            self._cache[key] = (1, [now])
        return False, 0
    
    def clear_expired(self):
        now = time.time()
        for key in list(self._cache.keys()):
            attempts, timestamps = self._cache[key]
            timestamps = [t for t in timestamps if now - t < 3600]
            if timestamps:
                self._cache[key] = (len(timestamps), timestamps)
            else:
                del self._cache[key]

rate_limiter = RateLimiter()

def rate_limit(key_prefix, max_attempts=5, timeout=300):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not settings.DEBUG:
                ip = request.META.get('REMOTE_ADDR', 'unknown')
                key = f"{key_prefix}:{ip}"
                is_limited, remaining = rate_limiter.is_rate_limited(key, max_attempts, timeout)
                if is_limited:
                    if request.headers.get('Accept') == 'application/json':
                        return JsonResponse({
                            'error': 'Too many requests. Please try again later.',
                            'retry_after': remaining
                        }, status=429)
                    from django.contrib import messages
                    messages.error(request, f'Too many attempts. Please try again in {remaining} seconds.')
                    return view_func(request, *args, **kwargs)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def send_verification_email(user, request):
    token = user.generate_email_verification_token()
    verify_url = f"{settings.SITE_DOMAIN}/accounts/verify-email/{token}/"
    
    subject = 'Verify your LocalKaam account'
    message = f"""
Hi {user.name},

Welcome to LocalKaam! Please verify your email address by clicking the link below:

{verify_url}

This link expires in 24 hours.

If you didn't create an account, please ignore this email.

Thanks,
LocalKaam Team
"""
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def send_password_reset_email(user, request):
    token = user.generate_password_reset_token()
    reset_url = f"{settings.SITE_DOMAIN}/accounts/reset-password/{token}/"
    
    subject = 'Reset your LocalKaam password'
    message = f"""
Hi {user.name},

You requested a password reset for your LocalKaam account. Click the link below to reset your password:

{reset_url}

This link expires in 1 hour.

If you didn't request a password reset, please ignore this email and your password will remain unchanged.

Thanks,
LocalKaam Team
"""
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False
