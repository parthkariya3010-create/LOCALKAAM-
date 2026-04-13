from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from functools import wraps
from django.http import JsonResponse
import time
import logging

# Set up email logging
logger = logging.getLogger(__name__)


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
                ip = request.META.get("REMOTE_ADDR", "unknown")
                key = f"{key_prefix}:{ip}"
                is_limited, remaining = rate_limiter.is_rate_limited(
                    key, max_attempts, timeout
                )
                if is_limited:
                    if request.headers.get("Accept") == "application/json":
                        return JsonResponse(
                            {
                                "error": "Too many requests. Please try again later.",
                                "retry_after": remaining,
                            },
                            status=429,
                        )
                    from django.contrib import messages

                    messages.error(
                        request,
                        f"Too many attempts. Please try again in {remaining} seconds.",
                    )
                    return view_func(request, *args, **kwargs)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def send_verification_email(user, request):
    """Send HTML email verification email with fallback to plain text"""
    token = user.generate_email_verification_token()
    verify_url = f"{settings.SITE_DOMAIN}/accounts/verify-email/{token}/"

    subject = "Verify your LocalKaam account"

    # Prepare context for template rendering
    context = {
        "user": user,
        "verify_url": verify_url,
        "support_url": f"{settings.SITE_DOMAIN}/support/",
        "unsubscribe_url": f"{settings.SITE_DOMAIN}/settings/notifications/",
        "privacy_url": f"{settings.SITE_DOMAIN}/privacy/",
        "terms_url": f"{settings.SITE_DOMAIN}/terms/",
        "current_year": timezone.now().year,
    }

    try:
        # Render HTML template
        html_message = render_to_string("emails/verification_email.html", context)
        # Strip HTML for plain text fallback
        plain_message = strip_tags(html_message)

        # Create email with both HTML and plain text versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        # Log successful email send
        logger.info(f"Verification email sent successfully to {user.email}")
        return True
    except Exception as e:
        # Log error
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        print(f"Email error: {e}")
        return False


def send_password_reset_email(user, request):
    """Send HTML email for password reset with fallback to plain text"""
    token = user.generate_password_reset_token()
    reset_url = f"{settings.SITE_DOMAIN}/accounts/reset-password/{token}/"

    subject = "Reset your LocalKaam password"

    # Prepare context for template rendering
    context = {
        "user": user,
        "reset_url": reset_url,
        "support_url": f"{settings.SITE_DOMAIN}/support/",
        "unsubscribe_url": f"{settings.SITE_DOMAIN}/settings/notifications/",
        "privacy_url": f"{settings.SITE_DOMAIN}/privacy/",
        "terms_url": f"{settings.SITE_DOMAIN}/terms/",
        "current_year": timezone.now().year,
    }

    try:
        # Render HTML template
        html_message = render_to_string("emails/password_reset_email.html", context)
        # Strip HTML for plain text fallback
        plain_message = strip_tags(html_message)

        # Create email with both HTML and plain text versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        # Log successful email send
        logger.info(f"Password reset email sent successfully to {user.email}")
        return True
    except Exception as e:
        # Log error
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        print(f"Email error: {e}")
        return False


def send_job_notification_email(user, job):
    """Send email notification for new job listing to matched workers"""
    subject = f"New Job Available: {job.title}"

    # Prepare context for template rendering
    context = {
        "user": user,
        "job": job,
        "view_job_url": f"{settings.SITE_DOMAIN}/jobs/{job.id}/",
        "current_year": timezone.now().year,
    }

    try:
        # Render HTML template
        html_message = render_to_string("emails/job_notification.html", context)
        # Strip HTML for plain text fallback
        plain_message = strip_tags(html_message)

        # Create email with both HTML and plain text versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        # Log successful email send
        logger.info(f"Job notification email sent to {user.email} for job {job.id}")
        return True
    except Exception as e:
        # Log error
        logger.error(f"Failed to send job notification email to {user.email}: {str(e)}")
        return False


def send_quotation_received_email(user, quotation):
    """Send email notification when a worker submits a quotation"""
    subject = f"New Quotation Received - {quotation.job.title}"

    context = {
        "user": user,
        "quotation": quotation,
        "worker_name": quotation.worker.name,
        "job_title": quotation.job.title,
        "view_quotation_url": f"{settings.SITE_DOMAIN}/quotations/{quotation.id}/",
        "current_year": timezone.now().year,
    }

    try:
        # Create plain text message
        plain_message = f"""
Hi {user.name},

{quotation.worker.name} has submitted a quotation for your job: {quotation.job.title}

Quotation Amount: ${quotation.amount}
Message: {quotation.message}

View the quotation: {context["view_quotation_url"]}

Best regards,
LocalKaam Team
"""

        # Send email
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        # Log successful email send
        logger.info(f"Quotation notification email sent to {user.email}")
        return True
    except Exception as e:
        # Log error
        logger.error(f"Failed to send quotation notification to {user.email}: {str(e)}")
        return False


def send_negotiation_update_email(user, negotiation):
    """Send email notification when negotiation status changes"""
    subject = f"Negotiation Update - {negotiation.job.title}"

    context = {
        "user": user,
        "negotiation": negotiation,
        "other_user": negotiation.worker
        if negotiation.customer == user
        else negotiation.customer,
        "job_title": negotiation.job.title,
        "status": negotiation.status,
        "view_negotiation_url": f"{settings.SITE_DOMAIN}/negotiations/{negotiation.id}/",
        "current_year": timezone.now().year,
    }

    try:
        # Create plain text message based on negotiation status
        if negotiation.status == "accepted":
            status_message = "has accepted your proposal"
        elif negotiation.status == "rejected":
            status_message = "has rejected your proposal"
        else:
            status_message = (
                f"has updated the negotiation status to {negotiation.status}"
            )

        plain_message = f"""
Hi {user.name},

{context["other_user"].name} {status_message} for the job: {negotiation.job.title}

View the negotiation details: {context["view_negotiation_url"]}

Best regards,
LocalKaam Team
"""

        # Send email
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        # Log successful email send
        logger.info(f"Negotiation update email sent to {user.email}")
        return True
    except Exception as e:
        # Log error
        logger.error(
            f"Failed to send negotiation update email to {user.email}: {str(e)}"
        )
        return False


def send_bulk_email(subject, recipients, plain_message=None, html_message=None):
    """
    Send bulk emails with logging and error handling.

    Args:
        subject: Email subject
        recipients: List of email addresses or User objects
        plain_message: Plain text message
        html_message: HTML message

    Returns:
        dict: {'success': count, 'failed': count, 'errors': list}
    """
    results = {"success": 0, "failed": 0, "errors": []}

    # Convert User objects to email addresses
    email_list = []
    for recipient in recipients:
        if hasattr(recipient, "email"):
            email_list.append(recipient.email)
        else:
            email_list.append(recipient)

    for email in email_list:
        try:
            if html_message:
                email_obj = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_message or strip_tags(html_message),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email],
                )
                email_obj.attach_alternative(html_message, "text/html")
                email_obj.send(fail_silently=False)
            else:
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )

            results["success"] += 1
            logger.info(f"Bulk email sent successfully to {email}")
        except Exception as e:
            results["failed"] += 1
            error_msg = f"Failed to send email to {email}: {str(e)}"
            results["errors"].append(error_msg)
            logger.error(error_msg)

    return results


# Email logging configuration
def configure_email_logging():
    """Configure logging for email operations"""
    if not logger.handlers:
        handler = logging.FileHandler("logs/email.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
