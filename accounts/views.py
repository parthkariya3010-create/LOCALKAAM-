from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.db import transaction
from django.utils import timezone
from django.http import HttpResponseRedirect, FileResponse, HttpResponse
from django.urls import resolve
from django.urls.exceptions import Resolver404
from django.core.exceptions import SuspiciousFileOperation
import os
import logging

logger = logging.getLogger(__name__)
from .forms import (
    UserRegistrationForm,
    UserLoginForm,
    JobForm,
    WorkerProfileForm,
    AvailabilityForm,
    QuotationForm,
    ReviewForm,
    UserProfileForm,
    NegotiationForm,
    NegotiationMessageForm,
)
from .models import (
    User,
    Job,
    WorkerProfile,
    Availability,
    Quotation,
    Review,
    UserProfile,
    Negotiation,
    NegotiationMessage,
    Favorite,
)
from .utils import rate_limit, send_verification_email, send_password_reset_email


def home(request):
    return render(request, "index.html")


@rate_limit(key_prefix="register", max_attempts=3, timeout=600)
def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            # Try to send verification email, but don't block registration if it fails
            try:
                send_verification_email(user, request)
                messages.success(
                    request,
                    "Registration successful! Please check your email to verify your account.",
                )
            except Exception as e:
                # Email sending failed, but allow registration to complete
                import logging

                logger = logging.getLogger(__name__)
                logger.error(
                    f"Email error during registration for {user.email}: {str(e)}"
                )
                messages.success(
                    request,
                    "Registration successful! However, we couldn't send the verification email. Please contact support.",
                )

            return redirect("login")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = UserRegistrationForm()
    return render(request, "register.html", {"form": form})


@login_required
def dashboard(request):
    # Refresh user from database to ensure latest data
    request.user.refresh_from_db()

    logger.info(
        f"Dashboard accessed by {request.user.email}, role: {request.user.role}"
    )

    # Ensure role is set (fallback to customer if empty)
    if not request.user.role or request.user.role == "":
        logger.warning(f"User {request.user.email} has empty role, setting to customer")
        request.user.role = "customer"
        request.user.save(update_fields=["role"])

    if request.user.role == "customer":
        logger.info(f"Redirecting customer {request.user.email} to customer_dashboard")
        return redirect("customer_dashboard")
    elif request.user.role == "worker":
        logger.info(f"Redirecting worker {request.user.email} to worker_dashboard")
        return redirect("worker_dashboard")
    else:
        # Fallback: set to customer and redirect
        logger.warning(
            f"Unknown role '{request.user.role}' for user {request.user.email}, setting to customer"
        )
        request.user.role = "customer"
        request.user.save(update_fields=["role"])
        return redirect("customer_dashboard")


@rate_limit(key_prefix="login", max_attempts=5, timeout=300)
def user_login(request):
    if request.user.is_authenticated:
        logger.info(
            f"User {request.user.email} already authenticated, redirecting to dashboard"
        )
        return redirect("dashboard")

    if request.method == "POST":
        form = UserLoginForm(request, data=request.POST)
        email = request.POST.get("username")

        try:
            user_obj = User.objects.get(email=email)
            if not user_obj.is_email_verified:
                logger.warning(f"Login attempt for unverified email: {email}")
                messages.warning(
                    request,
                    "Please verify your email first. Check your inbox for the verification link.",
                )
                return render(request, "login.html", {"form": form})
        except User.DoesNotExist:
            pass

        if form.is_valid():
            user = form.get_user()
            logger.info(f"User {user.email} (role: {user.role}) logged in successfully")
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect("dashboard")
        else:
            logger.warning(f"Login form validation failed for email: {email}")
    else:
        form = UserLoginForm()
    return render(request, "login.html", {"form": form})


def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def customer_dashboard(request):
    if request.user.role != "customer":
        return redirect("dashboard")
    jobs = (
        Job.objects.filter(customer=request.user)
        .select_related("worker")
        .order_by("-created_at")
    )
    jobs_open = jobs.filter(status="open").count()
    jobs_completed = jobs.filter(status="completed").count()

    from django.db.models import Count

    active_jobs = jobs.filter(status="confirmed").count()
    pending_quotations = (
        Quotation.objects.filter(job__customer=request.user, status="pending")
        .select_related("worker")
        .count()
    )

    active_negotiations = Negotiation.objects.filter(
        customer=request.user, status="active"
    ).order_by("-updated_at")

    return render(
        request,
        "customer_dashboard.html",
        {
            "jobs": jobs,
            "total_jobs": jobs.count(),
            "active_jobs": active_jobs,
            "completed_jobs": jobs_completed,
            "pending_quotations": pending_quotations,
            "active_negotiations": active_negotiations,
        },
    )


@login_required
def create_job(request):
    if request.user.role != "customer":
        return redirect("dashboard")

    if request.method == "POST":
        form = JobForm(request.POST, request.FILES)

        if "select_worker" in request.POST:
            worker_id = request.POST.get("worker_id")
            job_id = request.POST.get("job_id")
            worker = get_object_or_404(User, id=worker_id, role="worker")
            job = get_object_or_404(Job, id=job_id, customer=request.user)
            job.worker = worker
            job.status = "confirmed"
            job.save()
            messages.success(request, f"Job assigned to {worker.name}!")
            return redirect("customer_dashboard")

        if form.is_valid():
            job = form.save(commit=False)
            job.customer = request.user
            job.save()

            matching_workers = get_matching_workers(
                job.location, job.date, job.time_slot, job.category
            )

            if matching_workers:
                favorited_ids = list(
                    Favorite.objects.filter(customer=request.user).values_list(
                        "worker_id", flat=True
                    )
                )
                return render(
                    request,
                    "select_worker.html",
                    {
                        "form": form,
                        "job": job,
                        "workers": matching_workers,
                        "favorited_ids": favorited_ids,
                    },
                )

            messages.success(
                request, "Job created! No workers available for this slot."
            )
            return redirect("customer_dashboard")
    else:
        form = JobForm()
    return render(request, "create_job.html", {"form": form})


@login_required
def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, customer=request.user)

    if job.status != "open":
        messages.error(request, "You can only edit jobs that are still open.")
        return redirect("customer_dashboard")

    if request.method == "POST":
        form = JobForm(request.POST, request.FILES, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, "Job updated successfully!")
            return redirect("customer_dashboard")
    else:
        form = JobForm(instance=job)

    return render(request, "edit_job.html", {"form": form, "job": job})


@login_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, customer=request.user)

    if job.status == "completed":
        messages.error(request, "You cannot delete completed jobs.")
        return redirect("customer_dashboard")

    if request.method == "POST":
        job.delete()
        messages.success(request, "Job deleted successfully!")
        return redirect("customer_dashboard")

    return render(request, "delete_job_confirm.html", {"job": job})


def get_matching_workers(location, date, time_slot, category):
    slot_map = {
        "morning": "morning",
        "afternoon": "afternoon",
        "evening": "evening",
    }

    mapped_slot = slot_map.get(time_slot.lower().strip(), "full_day")

    availability_filter = Q(date=date) & (
        Q(time_slot=mapped_slot) | Q(time_slot="full_day")
    )

    available_workers = Availability.objects.filter(availability_filter).values_list(
        "worker_id", flat=True
    )

    workers = User.objects.filter(
        id__in=available_workers,
        location__iexact=location,
        role="worker",
        worker_profile__skills__icontains=category,
    ).select_related("worker_profile")

    return workers


def get_worker_time_slot(time_str):
    time_str = time_str.lower().strip()

    if "morning" in time_str:
        return "morning"
    elif "afternoon" in time_str:
        return "afternoon"
    elif "evening" in time_str:
        return "evening"
    elif "full" in time_str or "day" in time_str:
        return "full_day"

    if "9:00" in time_str and "12:00" in time_str:
        return "morning"
    elif "12:00" in time_str and "18:00" in time_str:
        return "afternoon"
    elif "18:00" in time_str and "22:00" in time_str:
        return "evening"

    return "morning"


@login_required
def worker_dashboard(request):
    if request.user.role != "worker":
        return redirect("dashboard")

    worker = request.user
    profile = getattr(worker, "worker_profile", None)

    if not profile:
        messages.warning(request, "Please complete your worker profile first.")
        return redirect("worker_profile")

    worker_skills_raw = profile.skills
    if worker_skills_raw.startswith("["):
        import ast

        try:
            worker_skills = [
                s.strip().lower() for s in ast.literal_eval(worker_skills_raw)
            ]
        except (ValueError, SyntaxError):
            worker_skills = [
                s.strip().lower() for s in worker_skills_raw.split(",") if s.strip()
            ]
    else:
        worker_skills = [
            s.strip().lower() for s in worker_skills_raw.split(",") if s.strip()
        ]

    availabilities = Availability.objects.filter(
        worker=worker, date__gte=timezone.now().date()
    )
    available_slots = set()
    for avail in availabilities:
        available_slots.add(avail.time_slot)

    jobs = Job.objects.filter(status="open").order_by("-created_at")

    matched_jobs = []
    for job in jobs:
        location_match = (
            profile.location
            and job.location.lower().strip() == profile.location.lower().strip()
        )
        skill_match = job.category.lower() in worker_skills or "other" in worker_skills

        if "full_day" in available_slots:
            time_slot_match = True
        else:
            time_slot_match = available_slots and job.time_slot in available_slots

        if location_match and skill_match and time_slot_match:
            matched_jobs.append(job)

    confirmed_jobs = Job.objects.filter(worker=worker, status="confirmed").order_by(
        "date"
    )
    completed_jobs = Job.objects.filter(
        worker=worker, status="completed"
    ).prefetch_related("quotations")
    completed_jobs_count = completed_jobs.count()

    total_earnings = sum(
        quotation.offered_price
        for job in completed_jobs
        for quotation in job.quotations.filter(status="accepted")
    )

    active_negotiations = Negotiation.objects.filter(
        worker=worker, status="active"
    ).order_by("-updated_at")

    return render(
        request,
        "worker_dashboard.html",
        {
            "jobs": matched_jobs,
            "confirmed_jobs": confirmed_jobs,
            "profile": profile,
            "completed_jobs_count": completed_jobs_count,
            "total_earnings": total_earnings,
            "active_negotiations": active_negotiations,
        },
    )


@login_required
def worker_profile(request):
    if request.user.role != "worker":
        return redirect("dashboard")

    try:
        profile = WorkerProfile.objects.get(user=request.user)
    except WorkerProfile.DoesNotExist:
        profile = None

    skill_choices = [
        ("plumbing", "Plumbing"),
        ("electrical", "Electrical"),
        ("cleaning", "Cleaning"),
        ("painting", "Painting"),
        ("carpentry", "Carpentry"),
        ("gardening", "Gardening"),
        ("moving", "Moving"),
        ("ac", "AC Technician"),
        ("appliance", "Appliance Repair"),
        ("other", "Other"),
    ]

    if request.method == "POST":
        form = WorkerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user

            skills_data = request.POST.get("skills", "")
            profile.skills = skills_data

            profile.location = request.POST.get("location", "")

            profile.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("worker_dashboard")
    else:
        form = WorkerProfileForm(instance=profile)

    return render(
        request,
        "worker_profile.html",
        {
            "form": form,
            "profile": profile,
            "skill_choices": skill_choices,
            "empty_list": [],
        },
    )


@login_required
def manage_availability(request):
    if request.user.role != "worker":
        return redirect("dashboard")

    if request.method == "POST":
        date_str = request.POST.get("date")
        time_slot = request.POST.get("time_slot")

        if date_str and time_slot:
            try:
                from datetime import datetime

                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

                availability = Availability(
                    worker=request.user, date=date_obj, time_slot=time_slot
                )
                availability.save()
                messages.success(request, "Availability added successfully!")
            except Exception as e:
                messages.error(request, "Invalid date or time slot.")
        else:
            messages.error(request, "Please fill all fields.")
        return redirect("manage_availability")

    form = AvailabilityForm()
    availabilities = Availability.objects.filter(worker=request.user).order_by("date")
    return render(
        request,
        "manage_availability.html",
        {"form": form, "availabilities": availabilities},
    )


@login_required
def delete_availability(request, availability_id):
    if request.user.role != "worker":
        return redirect("dashboard")

    availability = get_object_or_404(
        Availability, id=availability_id, worker=request.user
    )
    availability.delete()
    messages.success(request, "Availability removed.")
    return redirect("manage_availability")


@login_required
def submit_quotation(request, job_id):
    if request.user.role != "worker":
        return redirect("dashboard")

    job = get_object_or_404(Job, id=job_id, status="open")

    existing_quotation = Quotation.objects.filter(job=job, worker=request.user).first()
    if existing_quotation:
        messages.error(request, "You have already submitted a quotation for this job.")
        return redirect("worker_dashboard")

    if request.method == "POST":
        form = QuotationForm(request.POST)
        if form.is_valid():
            quotation = form.save(commit=False)
            quotation.job = job
            quotation.worker = request.user
            quotation.save()
            messages.success(request, "Quotation submitted successfully!")
            return redirect("worker_dashboard")
    else:
        form = QuotationForm()

    return render(request, "submit_quotation.html", {"form": form, "job": job})


@login_required
def view_quotations(request, job_id):
    if request.user.role != "customer":
        return redirect("dashboard")

    job = get_object_or_404(Job, id=job_id, customer=request.user)
    quotations = Quotation.objects.filter(job=job).select_related(
        "worker__worker_profile"
    )

    return render(
        request, "view_quotations.html", {"job": job, "quotations": quotations}
    )


@login_required
@transaction.atomic
def accept_quotation(request, quotation_id):
    if request.user.role != "customer":
        return redirect("dashboard")

    quotation = get_object_or_404(
        Quotation, id=quotation_id, job__customer=request.user, status="pending"
    )

    worker = quotation.worker
    job_date = quotation.job.date

    conflicting_jobs = Job.objects.filter(
        worker=worker, date=job_date, status__in=["open", "confirmed"]
    ).exists()

    if conflicting_jobs:
        messages.error(
            request,
            f"Worker {worker.name} already has a job on {job_date}. Cannot accept this quotation.",
        )
        return redirect("view_quotations", job_id=quotation.job.id)

    quotation.status = "accepted"
    quotation.save()

    job = quotation.job
    job.worker = worker
    job.status = "confirmed"
    job.save()

    Quotation.objects.filter(job=job).exclude(id=quotation_id).update(status="rejected")

    job_time_slot = get_worker_time_slot(job.time_slot)
    Availability.objects.filter(
        worker=worker, date=job_date, time_slot=job_time_slot
    ).delete()

    messages.success(request, f"Quotation accepted! Job assigned to {worker.name}")
    return redirect("customer_dashboard")


@login_required
def reject_quotation(request, quotation_id):
    if request.user.role != "customer":
        return redirect("dashboard")

    quotation = get_object_or_404(
        Quotation, id=quotation_id, job__customer=request.user, status="pending"
    )
    quotation.status = "rejected"
    quotation.save()

    messages.success(request, "Quotation rejected.")
    return redirect("view_quotations", job_id=quotation.job.id)


@login_required
def mark_job_completed(request, job_id):
    if request.user.role != "worker":
        return redirect("dashboard")

    job = get_object_or_404(Job, id=job_id, worker=request.user, status="confirmed")
    job.status = "completed"
    job.save()

    messages.success(request, "Job marked as completed!")
    return redirect("worker_dashboard")


@login_required
def create_review(request, job_id):
    if request.user.role != "customer":
        return redirect("dashboard")

    job = get_object_or_404(Job, id=job_id, customer=request.user, status="completed")

    if hasattr(job, "review"):
        messages.error(request, "You have already reviewed this job.")
        return redirect("customer_dashboard")

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.job = job
            review.customer = request.user
            review.worker = job.worker
            review.save()

            # Check if worker profile exists before updating rating
            if hasattr(job.worker, "worker_profile") and job.worker.worker_profile:
                worker_profile = job.worker.worker_profile
                avg_rating = Review.objects.filter(worker=job.worker).aggregate(
                    Avg("rating")
                )["rating__avg"]
                worker_profile.avg_rating = round(avg_rating, 2) if avg_rating else 0.00
                worker_profile.save()

            messages.success(request, "Review submitted successfully!")
            return redirect("customer_dashboard")
    else:
        form = ReviewForm()

    return render(request, "create_review.html", {"form": form, "job": job})


@login_required
def profile_view(request):
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = None

    return render(
        request, "profile.html", {"profile": user_profile, "user": request.user}
    )


@login_required
def edit_profile(request):
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        user_profile = None

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, "edit_profile.html", {"form": form, "profile": user_profile})


@login_required
def start_negotiation(request, quotation_id):
    if request.user.role != "customer":
        return redirect("dashboard")

    quotation = get_object_or_404(
        Quotation, id=quotation_id, job__customer=request.user
    )

    existing_negotiation = Negotiation.objects.filter(
        quotation=quotation, worker=quotation.worker
    ).first()
    if existing_negotiation:
        return redirect("negotiation_detail", negotiation_id=existing_negotiation.id)

    if request.method == "POST":
        initial_price = request.POST.get("initial_price")
        message = request.POST.get("message", "")

        if not initial_price:
            messages.error(request, "Please enter a starting price for negotiation.")
            return redirect("start_negotiation", quotation_id=quotation_id)

        negotiation = Negotiation.objects.create(
            quotation=quotation,
            job=quotation.job,
            worker=quotation.worker,
            customer=request.user,
            current_price=initial_price,
        )

        NegotiationMessage.objects.create(
            negotiation=negotiation,
            sender=request.user,
            message_type="offer",
            price=initial_price,
            content=message or f"Starting negotiation at ₹{initial_price}",
        )

        messages.success(request, "Negotiation started! The worker will be notified.")
        return redirect("negotiation_detail", negotiation_id=negotiation.id)

    return render(request, "start_negotiation.html", {"quotation": quotation})


@login_required
def worker_start_negotiation(request, job_id):
    if request.user.role != "worker":
        return redirect("dashboard")

    job = get_object_or_404(Job, id=job_id)

    quotation = Quotation.objects.filter(job=job, worker=request.user).first()
    if not quotation:
        messages.error(request, "You need to submit a quotation first.")
        return redirect("worker_dashboard")

    existing_negotiation = Negotiation.objects.filter(
        quotation=quotation, worker=request.user
    ).first()
    if existing_negotiation:
        return redirect("negotiation_detail", negotiation_id=existing_negotiation.id)

    if request.method == "POST":
        initial_price = request.POST.get("initial_price")
        message = request.POST.get("message", "")

        if not initial_price:
            messages.error(request, "Please enter a starting price for negotiation.")
            return redirect("worker_start_negotiation", job_id=job_id)

        negotiation = Negotiation.objects.create(
            quotation=quotation,
            job=job,
            worker=request.user,
            customer=job.customer,
            current_price=initial_price,
        )

        NegotiationMessage.objects.create(
            negotiation=negotiation,
            sender=request.user,
            message_type="offer",
            price=initial_price,
            content=message or f"Starting negotiation at ₹{initial_price}",
        )

        messages.success(request, "Negotiation started! The customer will be notified.")
        return redirect("negotiation_detail", negotiation_id=negotiation.id)

    return render(
        request, "worker_start_negotiation.html", {"job": job, "quotation": quotation}
    )


@login_required
@transaction.atomic
def negotiation_detail(request, negotiation_id):
    negotiation = get_object_or_404(Negotiation, id=negotiation_id)

    if request.user not in [negotiation.customer, negotiation.worker]:
        return redirect("dashboard")

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "send":
            form = NegotiationMessageForm(request.POST)
            if form.is_valid():
                msg_type = form.cleaned_data["message_type"]
                price = form.cleaned_data.get("price")
                content = form.cleaned_data["content"]

                NegotiationMessage.objects.create(
                    negotiation=negotiation,
                    sender=request.user,
                    message_type=msg_type,
                    price=price,
                    content=content,
                )

                if price:
                    negotiation.current_price = price
                    negotiation.save()

                messages.success(request, "Message sent!")
                return redirect("negotiation_detail", negotiation_id=negotiation.id)

        elif action == "accept":
            if request.user != negotiation.worker:
                messages.error(
                    request, "You are not authorized to accept this negotiation."
                )
                return redirect("negotiation_detail", negotiation_id=negotiation.id)

            negotiation.status = "accepted"
            negotiation.save()

            NegotiationMessage.objects.create(
                negotiation=negotiation,
                sender=request.user,
                message_type="accept",
                content=f"Negotiation accepted at ₹{negotiation.current_price}",
            )

            quotation = negotiation.quotation
            quotation.status = "accepted"
            quotation.save()

            job = negotiation.job
            job.worker = negotiation.worker
            job.status = "confirmed"
            job.save()

            Quotation.objects.filter(job=job).exclude(id=quotation.id).update(
                status="rejected"
            )

            Availability.objects.filter(
                worker=negotiation.worker,
                date=job.date,
                time_slot=get_worker_time_slot(job.time_slot),
            ).delete()

            messages.success(
                request,
                f"Negotiation accepted! Job confirmed with {negotiation.worker.name}",
            )
            return redirect("worker_dashboard")

        elif action == "reject":
            if request.user != negotiation.worker:
                messages.error(
                    request, "You are not authorized to reject this negotiation."
                )
                return redirect("negotiation_detail", negotiation_id=negotiation.id)

            negotiation.status = "rejected"
            negotiation.save()

            NegotiationMessage.objects.create(
                negotiation=negotiation,
                sender=request.user,
                message_type="reject",
                content="Negotiation rejected",
            )

            messages.info(request, "Negotiation rejected.")
            return redirect("negotiation_detail", negotiation_id=negotiation.id)

        elif action == "cancel":
            if request.user != negotiation.customer:
                messages.error(
                    request, "You are not authorized to cancel this negotiation."
                )
                return redirect("negotiation_detail", negotiation_id=negotiation.id)

            negotiation.status = "cancelled"
            negotiation.save()

            NegotiationMessage.objects.create(
                negotiation=negotiation,
                sender=request.user,
                message_type="reject",
                content="Negotiation cancelled",
            )

            messages.info(request, "Negotiation cancelled.")
            return redirect(
                "customer_dashboard"
                if request.user.role == "customer"
                else "worker_dashboard"
            )

    form = NegotiationMessageForm()
    messages_list = negotiation.messages.all().order_by("created_at")

    return render(
        request,
        "negotiation_detail.html",
        {"negotiation": negotiation, "form": form, "messages": messages_list},
    )


@login_required
def customer_negotiations(request):
    if request.user.role != "customer":
        return redirect("dashboard")

    negotiations = Negotiation.objects.filter(customer=request.user).order_by(
        "-updated_at"
    )
    return render(request, "customer_negotiations.html", {"negotiations": negotiations})


@login_required
def worker_negotiations(request):
    if request.user.role != "worker":
        return redirect("dashboard")

    negotiations = Negotiation.objects.filter(worker=request.user).order_by(
        "-updated_at"
    )
    return render(request, "worker_negotiations.html", {"negotiations": negotiations})


@rate_limit(
    key_prefix="verify_email", max_attempts=10, timeout=60, use_token_arg="token"
)
def verify_email(request, token):
    try:
        user = User.objects.get(email_verification_token=token)

        if user.is_email_verified:
            messages.info(request, "Email already verified.")
            return redirect("login")

        if user.verify_email(token):
            messages.success(request, "Email verified successfully! You can now login.")
        else:
            messages.error(request, "Invalid or expired verification link.")

        return redirect("login")
    except User.DoesNotExist:
        messages.error(request, "Invalid verification link.")
        return redirect("login")


@rate_limit(key_prefix="resend_verification", max_attempts=3, timeout=600)
def resend_verification(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            if user.is_email_verified:
                messages.info(request, "Email already verified.")
                return redirect("login")

            send_verification_email(user, request)
            messages.success(
                request, "Verification email sent! Please check your inbox."
            )
        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")

    return render(request, "resend_verification.html")


@rate_limit(key_prefix="password_reset", max_attempts=3, timeout=600)
def password_reset_request(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(user, request)
            messages.success(
                request, "Password reset email sent! Please check your inbox."
            )
            return redirect("login")
        except User.DoesNotExist:
            messages.error(request, "No account found with this email.")

    return render(request, "password_reset_request.html")


@login_required
def toggle_favorite(request, worker_id):
    if request.user.role != "customer":
        return redirect("dashboard")

    worker = get_object_or_404(User, id=worker_id, role="worker")

    favorite = Favorite.objects.filter(customer=request.user, worker=worker).first()

    if favorite:
        favorite.delete()
        messages.success(request, f"{worker.name} removed from favorites")
    else:
        Favorite.objects.create(customer=request.user, worker=worker)
        messages.success(request, f"{worker.name} added to favorites!")

    # Safe redirect using referer or default
    referer = request.META.get("HTTP_REFERER", "")
    if referer:
        try:
            # Validate that the referer is from our own domain
            from urllib.parse import urlparse

            referer_host = urlparse(referer).netloc
            request_host = request.get_host()
            if referer_host == request_host:
                return HttpResponseRedirect(referer)
        except:
            pass

    return redirect("customer_dashboard")


@login_required
def favorites_list(request):
    if request.user.role != "customer":
        return redirect("dashboard")

    favorites = Favorite.objects.filter(customer=request.user).select_related(
        "worker__worker_profile"
    )

    return render(request, "favorites.html", {"favorites": favorites})


def password_reset_confirm(request, token):
    try:
        user = User.objects.get(password_reset_token=token)

        if request.method == "POST":
            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")

            if password1 != password2:
                messages.error(request, "Passwords do not match.")
                return render(request, "password_reset_confirm.html", {"token": token})

            if len(password1) < 8:
                messages.error(request, "Password must be at least 8 characters.")
                return render(request, "password_reset_confirm.html", {"token": token})

            if user.reset_password(token, password1):
                messages.success(
                    request,
                    "Password reset successful! Please login with your new password.",
                )
                return redirect("login")
            else:
                messages.error(request, "Invalid or expired reset link.")
                return redirect("login")

        return render(request, "password_reset_confirm.html", {"token": token})
    except User.DoesNotExist:
        messages.error(request, "Invalid reset link.")
        return redirect("login")


# Website informational pages
def features(request):
    """Display features page"""
    return render(request, "features.html")


def how_it_works(request):
    """Display how it works page"""
    return render(request, "how_it_works.html")


def services(request):
    """Display services page"""
    return render(request, "services.html")


def about_us(request):
    """Display about us page"""
    return render(request, "about_us.html")


def contact_us(request):
    """Handle contact us form submissions and display contact page"""
    from django.core.mail import send_mail
    from django.http import JsonResponse

    if request.method == "POST":
        # Get form data
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        subject = request.POST.get("subject", "").strip()
        category = request.POST.get("category", "").strip()
        message = request.POST.get("message", "").strip()

        # Validate required fields
        if not all([name, email, subject, category, message]):
            return JsonResponse(
                {"success": False, "message": "Please fill in all required fields."},
                status=400,
            )

        # Validate email format
        from django.core.validators import validate_email, ValidationError

        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse(
                {"success": False, "message": "Please enter a valid email address."},
                status=400,
            )

        try:
            # Prepare email content
            contact_email = os.getenv("CONTACT_EMAIL", "official.localkaam@gmail.com")

            email_subject = f"New Contact Form Submission: {subject}"

            email_body = f"""
New Contact Form Submission

Name: {name}
Email: {email}
Phone: {phone if phone else "Not provided"}
Category: {category}
Subject: {subject}

Message:
{message}

---
This is an automated message from LocalKaam contact form.
"""

            # Send email to admin
            send_mail(
                email_subject,
                email_body,
                os.getenv("EMAIL_HOST_USER", "official.localkaam@gmail.com"),
                [contact_email],
                fail_silently=False,
            )

            # Also send confirmation email to user
            user_email_subject = "We received your message - LocalKaam"
            user_email_body = f"""
Hello {name},

Thank you for reaching out to LocalKaam. We have received your message and will get back to you as soon as possible.

Your submission details:
- Subject: {subject}
- Category: {category}
- Message: {message[:100]}...

We typically respond within 24 hours.

Best regards,
LocalKaam Team
official.localkaam@gmail.com
+91 8766554942
"""

            send_mail(
                user_email_subject,
                user_email_body,
                os.getenv("EMAIL_HOST_USER", "official.localkaam@gmail.com"),
                [email],
                fail_silently=True,
            )

            return JsonResponse(
                {
                    "success": True,
                    "message": "Thank you! Your message has been sent successfully. We'll contact you soon.",
                }
            )

        except Exception as e:
            import traceback

            error_msg = str(e)
            error_trace = traceback.format_exc()
            print(f"Error sending email: {error_msg}")
            print(f"Full traceback:\n{error_trace}")
            return JsonResponse(
                {
                    "success": False,
                    "message": f"Error sending message: {error_msg}",
                },
                status=500,
            )

    # For GET requests, just display the contact page
    return render(request, "contact_us.html")


def serve_media(request, filepath):
    """
    Serve media files safely
    """
    try:
        from django.conf import settings

        full_path = os.path.join(settings.MEDIA_ROOT, filepath)

        # Security check - ensure path is within MEDIA_ROOT
        full_path = os.path.abspath(full_path)
        media_root = os.path.abspath(settings.MEDIA_ROOT)

        if not full_path.startswith(media_root):
            raise SuspiciousFileOperation("Attempted access outside MEDIA_ROOT")

        if not os.path.exists(full_path):
            return HttpResponse("File not found", status=404)

        return FileResponse(open(full_path, "rb"), content_type="image/jpeg")
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)
