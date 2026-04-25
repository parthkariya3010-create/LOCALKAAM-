import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from decimal import Decimal
from accounts.models import (
    User,
    UserProfile,
    Job,
    WorkerProfile,
    Availability,
    Quotation,
    Review,
    Negotiation,
    Favorite,
    NegotiationMessage,
)


class UserModelTest(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "username": "testuser",
            "role": "customer",
        }

    def test_user_creation(self):
        """Test basic user creation"""
        user = User.objects.create(**self.user_data)
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.name, "Test User")
        self.assertEqual(user.role, "customer")
        self.assertFalse(user.is_email_verified)
        self.assertEqual(str(user), "test@example.com")

    def test_user_roles(self):
        """Test user role choices"""
        customer = User.objects.create(
            email="customer@example.com",
            name="Customer User",
            username="customer_user",
            role="customer",
        )
        worker = User.objects.create(
            email="worker@example.com",
            name="Worker User",
            username="worker_user",
            role="worker",
        )
        self.assertEqual(customer.role, "customer")
        self.assertEqual(worker.role, "worker")

    def test_email_verification_token_generation(self):
        """Test email verification token generation"""
        user = User.objects.create(**self.user_data)
        token = user.generate_email_verification_token()

        self.assertIsNotNone(token)
        self.assertIsNotNone(user.email_verification_token)
        self.assertIsNotNone(user.email_verification_sent_at)
        self.assertTrue(len(token) > 0)

    def test_email_verification_success(self):
        """Test successful email verification"""
        user = User.objects.create(**self.user_data)
        token = user.generate_email_verification_token()

        # Set sent time to within 24 hours
        user.email_verification_sent_at = timezone.now() - timedelta(hours=1)
        user.save()

        result = user.verify_email(token)
        self.assertTrue(result)
        self.assertTrue(user.is_email_verified)
        self.assertTrue(user.is_active)
        self.assertEqual(user.email_verification_token, "")

    def test_email_verification_expired_token(self):
        """Test email verification with expired token"""
        user = User.objects.create(**self.user_data)
        token = user.generate_email_verification_token()

        # Set sent time to more than 24 hours ago
        user.email_verification_sent_at = timezone.now() - timedelta(hours=25)
        user.save()

        result = user.verify_email(token)
        self.assertFalse(result)
        self.assertFalse(user.is_email_verified)

    def test_password_reset_token_generation(self):
        """Test password reset token generation"""
        user = User.objects.create(**self.user_data)
        token = user.generate_password_reset_token()

        self.assertIsNotNone(token)
        self.assertIsNotNone(user.password_reset_token)
        self.assertIsNotNone(user.password_reset_sent_at)

    def test_password_reset_success(self):
        """Test successful password reset"""
        user = User.objects.create(**self.user_data)
        token = user.generate_password_reset_token()

        # Set sent time to within 1 hour
        user.password_reset_sent_at = timezone.now() - timedelta(minutes=30)
        user.save()

        result = user.reset_password(token, "newpassword123")
        self.assertTrue(result)
        self.assertTrue(user.check_password("newpassword123"))
        self.assertEqual(user.password_reset_token, "")

    def test_password_reset_expired_token(self):
        """Test password reset with expired token"""
        user = User.objects.create(**self.user_data)
        token = user.generate_password_reset_token()

        # Set sent time to more than 1 hour ago
        user.password_reset_sent_at = timezone.now() - timedelta(hours=2)
        user.save()

        result = user.reset_password(token, "newpassword123")
        self.assertFalse(result)


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            email="test@example.com",
            name="Test User",
            username="testuser",
            role="customer",
        )

    def test_user_profile_creation(self):
        """Test user profile creation"""
        profile = UserProfile.objects.create(
            user=self.user,
            phone_number="1234567890",
            address="123 Test Street",
            gender="male",
        )
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.phone_number, "1234567890")
        self.assertEqual(str(profile), f"Profile of {self.user.name}")

    def test_phone_number_validation(self):
        """Test phone number validation"""
        # Valid phone number
        profile = UserProfile(user=self.user, phone_number="1234567890")
        profile.full_clean()  # Should not raise ValidationError

        # Invalid phone number (too short)
        with self.assertRaises(ValidationError):
            invalid_profile = UserProfile(user=self.user, phone_number="12345")
            invalid_profile.full_clean()


class WorkerProfileModelTest(TestCase):
    def setUp(self):
        self.worker = User.objects.create(
            email="worker@example.com",
            name="Worker User",
            username="worker",
            role="worker",
        )

    def test_worker_profile_creation(self):
        """Test worker profile creation"""
        profile = WorkerProfile.objects.create(
            user=self.worker,
            skills="plumbing,electrical",
            experience=5,
            base_price=Decimal("500.00"),
            location="Test City",
        )
        self.assertEqual(profile.user, self.worker)
        self.assertEqual(profile.skills, "plumbing,electrical")
        self.assertEqual(profile.experience, 5)
        self.assertEqual(profile.base_price, Decimal("500.00"))
        self.assertEqual(str(profile), f"{self.worker.name} - plumbing,electrical")

    def test_skills_list_property(self):
        """Test skills_list property"""
        profile = WorkerProfile.objects.create(
            user=self.worker,
            skills="plumbing, electrical, painting",
            experience=3,
            base_price=Decimal("300.00"),
        )
        expected_skills = ["plumbing", "electrical", "painting"]
        self.assertEqual(profile.skills_list, expected_skills)

    def test_base_price_validation(self):
        """Test base price validation"""
        # Valid price
        profile = WorkerProfile(
            user=self.worker,
            skills="plumbing",
            experience=1,
            base_price=Decimal("0.01"),
        )
        profile.full_clean()  # Should not raise ValidationError

        # Invalid price (too low)
        with self.assertRaises(ValidationError):
            invalid_profile = WorkerProfile(
                user=self.worker,
                skills="plumbing",
                experience=1,
                base_price=Decimal("0.00"),
            )
            invalid_profile.full_clean()


class JobModelTest(TestCase):
    def setUp(self):
        self.customer = User.objects.create(
            email="customer@example.com",
            name="Customer User",
            username="customer",
            role="customer",
        )

    def test_job_creation(self):
        """Test job creation"""
        job = Job.objects.create(
            customer=self.customer,
            category="plumbing",
            location="Test City",
            date=timezone.now().date(),
            time_slot="morning",
        )
        self.assertEqual(job.customer, self.customer)
        self.assertEqual(job.category, "plumbing")
        self.assertEqual(job.status, "open")
        self.assertEqual(str(job), f"plumbing - Test City - {job.date}")

    def test_job_status_choices(self):
        """Test job status choices"""
        job = Job.objects.create(
            customer=self.customer,
            category="electrical",
            location="Test City",
            date=timezone.now().date(),
            time_slot="afternoon",
        )

        # Test status changes
        job.status = "confirmed"
        job.save()
        self.assertEqual(job.status, "confirmed")

        job.status = "completed"
        job.save()
        self.assertEqual(job.status, "completed")


class QuotationModelTest(TestCase):
    def setUp(self):
        self.customer = User.objects.create(
            email="customer@example.com",
            name="Customer User",
            username="customer",
            role="customer",
        )
        self.worker = User.objects.create(
            email="worker@example.com",
            name="Worker User",
            username="worker",
            role="worker",
        )
        self.job = Job.objects.create(
            customer=self.customer,
            category="plumbing",
            location="Test City",
            date=timezone.now().date(),
            time_slot="morning",
        )

    def test_quotation_creation(self):
        """Test quotation creation"""
        quotation = Quotation.objects.create(
            job=self.job,
            worker=self.worker,
            offered_price=Decimal("600.00"),
            message="I can fix your plumbing issue.",
        )
        self.assertEqual(quotation.job, self.job)
        self.assertEqual(quotation.worker, self.worker)
        self.assertEqual(quotation.offered_price, Decimal("600.00"))
        self.assertEqual(quotation.status, "pending")
        self.assertEqual(
            str(quotation), f"Quotation by {self.worker.name} for plumbing - ₹600.00"
        )

    def test_quotation_unique_constraint(self):
        """Test unique constraint on job-worker combination"""
        Quotation.objects.create(
            job=self.job, worker=self.worker, offered_price=Decimal("600.00")
        )

        # Should raise IntegrityError
        with self.assertRaises(Exception):  # Could be IntegrityError or ValidationError
            Quotation.objects.create(
                job=self.job, worker=self.worker, offered_price=Decimal("700.00")
            )


class AvailabilityModelTest(TestCase):
    def setUp(self):
        self.worker = User.objects.create(
            email="worker@example.com",
            name="Worker User",
            username="worker",
            role="worker",
        )

    def test_availability_creation(self):
        """Test availability creation"""
        availability = Availability.objects.create(
            worker=self.worker, date=timezone.now().date(), time_slot="morning"
        )
        self.assertEqual(availability.worker, self.worker)
        self.assertEqual(availability.time_slot, "morning")
        self.assertTrue(availability.is_available)
        self.assertEqual(
            str(availability), f"{self.worker.name} - {availability.date} - morning"
        )

    def test_availability_unique_constraint(self):
        """Test unique constraint on worker-date-timeslot combination"""
        date = timezone.now().date()
        Availability.objects.create(worker=self.worker, date=date, time_slot="morning")

        # Should raise IntegrityError
        with self.assertRaises(Exception):
            Availability.objects.create(
                worker=self.worker, date=date, time_slot="morning"
            )


class ReviewModelTest(TestCase):
    def setUp(self):
        self.customer = User.objects.create(
            email="customer@example.com",
            name="Customer User",
            username="customer",
            role="customer",
        )
        self.worker = User.objects.create(
            email="worker@example.com",
            name="Worker User",
            username="worker",
            role="worker",
        )
        self.job = Job.objects.create(
            customer=self.customer,
            worker=self.worker,
            category="plumbing",
            location="Test City",
            date=timezone.now().date(),
            time_slot="morning",
            status="completed",
        )

    def test_review_creation(self):
        """Test review creation"""
        review = Review.objects.create(
            job=self.job,
            customer=self.customer,
            worker=self.worker,
            rating=5,
            comment="Excellent service!",
        )
        self.assertEqual(review.job, self.job)
        self.assertEqual(review.customer, self.customer)
        self.assertEqual(review.worker, self.worker)
        self.assertEqual(review.rating, 5)
        self.assertEqual(
            str(review), f"Review by {self.customer.name} for {self.worker.name} - 5★"
        )


class FavoriteModelTest(TestCase):
    def setUp(self):
        self.customer = User.objects.create(
            email="customer@example.com",
            name="Customer User",
            username="customer",
            role="customer",
        )
        self.worker = User.objects.create(
            email="worker@example.com",
            name="Worker User",
            username="worker",
            role="worker",
        )

    def test_favorite_creation(self):
        """Test favorite creation"""
        favorite = Favorite.objects.create(customer=self.customer, worker=self.worker)
        self.assertEqual(favorite.customer, self.customer)
        self.assertEqual(favorite.worker, self.worker)
        self.assertEqual(
            str(favorite), f"{self.customer.name} favorited {self.worker.name}"
        )

    def test_favorite_unique_constraint(self):
        """Test unique constraint on customer-worker combination"""
        Favorite.objects.create(customer=self.customer, worker=self.worker)

        # Should raise IntegrityError
        with self.assertRaises(Exception):
            Favorite.objects.create(customer=self.customer, worker=self.worker)
