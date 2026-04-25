import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from accounts.forms import (
    UserRegistrationForm,
    UserLoginForm,
    JobForm,
    WorkerProfileForm,
    QuotationForm,
    ReviewForm,
    UserProfileForm,
    NegotiationMessageForm,
)


class UserRegistrationFormTest(TestCase):
    def test_valid_registration_form(self):
        """Test valid user registration form"""
        form_data = {
            "name": "Test User",
            "email": "test@example.com",
            "role": "customer",
            "location": "Test City",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_registration_form_password_mismatch(self):
        """Test registration form with mismatched passwords"""
        form_data = {
            "name": "Test User",
            "email": "test@example.com",
            "role": "customer",
            "password1": "testpass123",
            "password2": "differentpass",
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_registration_form_save_creates_username(self):
        """Test that saving registration form creates a unique username"""
        form_data = {
            "name": "Test User",
            "email": "test@example.com",
            "role": "customer",
            "password1": "testpass123",
            "password2": "testpass123",
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertIsNotNone(user.username)
        self.assertTrue(user.username.startswith("user_"))


class JobFormTest(TestCase):
    def test_valid_job_form(self):
        """Test valid job form"""
        future_date = timezone.now().date() + timedelta(days=1)
        form_data = {
            "category": "plumbing",
            "exact_location": "123 Test Street",
            "location": "Sion",
            "date": future_date,
            "time_slot": "morning",
        }
        form = JobForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_job_form_past_date_validation(self):
        """Test job form rejects past dates"""
        past_date = timezone.now().date() - timedelta(days=1)
        form_data = {
            "category": "plumbing",
            "exact_location": "123 Test Street",
            "location": "Sion",
            "date": past_date,
            "time_slot": "morning",
        }
        form = JobForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("date", form.errors)
        self.assertIn("Job date must be in the future", str(form.errors["date"]))

    def test_job_form_invalid_location_choice(self):
        """Test job form with invalid location choice"""
        future_date = timezone.now().date() + timedelta(days=1)
        form_data = {
            "category": "plumbing",
            "exact_location": "123 Test Street",
            "location": "Invalid City",
            "date": future_date,
            "time_slot": "morning",
        }
        form = JobForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("location", form.errors)


class WorkerProfileFormTest(TestCase):
    def test_valid_worker_profile_form(self):
        """Test valid worker profile form"""
        form_data = {
            "skills": "plumbing,electrical",
            "experience": 5,
            "base_price": "500.00",
            "location": "Sion",
        }
        form = WorkerProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_worker_profile_skills_cleaning_list(self):
        """Test skills field cleaning with list input"""
        form_data = {
            "skills": ["plumbing", "electrical"],
            "experience": 5,
            "base_price": "500.00",
            "location": "Sion",
        }
        form = WorkerProfileForm(data=form_data)
        self.assertTrue(form.is_valid())
        # When Django processes list input, it becomes a string representation
        self.assertEqual(form.cleaned_data["skills"], "['plumbing', 'electrical']")

    def test_worker_profile_skills_cleaning_string(self):
        """Test skills field cleaning with string input"""
        form_data = {
            "skills": "plumbing,electrical",
            "experience": 5,
            "base_price": "500.00",
            "location": "Sion",
        }
        form = WorkerProfileForm(data=form_data)
        self.assertTrue(form.is_valid())
        cleaned_skills = form.clean_skills()
        self.assertEqual(cleaned_skills, "plumbing,electrical")


class QuotationFormTest(TestCase):
    def test_valid_quotation_form(self):
        """Test valid quotation form"""
        form_data = {
            "offered_price": "600.00",
            "message": "I can fix your plumbing issue.",
        }
        form = QuotationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_quotation_form_without_message(self):
        """Test quotation form without optional message"""
        form_data = {"offered_price": "600.00", "message": ""}
        form = QuotationForm(data=form_data)
        self.assertTrue(form.is_valid())


class ReviewFormTest(TestCase):
    def test_valid_review_form(self):
        """Test valid review form"""
        form_data = {"rating": 5, "comment": "Excellent service!"}
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_review_form_without_comment(self):
        """Test review form without optional comment"""
        form_data = {"rating": 4, "comment": ""}
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())


class UserProfileFormTest(TestCase):
    def test_valid_user_profile_form(self):
        """Test valid user profile form"""
        form_data = {
            "phone_number": "1234567890",
            "address": "123 Test Street",
            "gender": "male",
            "bio": "I am a test user",
            "emergency_contact": "0987654321",
        }
        form = UserProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_user_profile_form_optional_fields(self):
        """Test user profile form with only required fields"""
        form_data = {"phone_number": "1234567890"}
        form = UserProfileForm(data=form_data)
        self.assertTrue(form.is_valid())


class NegotiationMessageFormTest(TestCase):
    def test_valid_negotiation_message_form_text(self):
        """Test valid negotiation message form with text type"""
        form_data = {
            "message_type": "text",
            "content": "Hello, can we discuss the price?",
        }
        form = NegotiationMessageForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_valid_negotiation_message_form_offer(self):
        """Test valid negotiation message form with offer type"""
        form_data = {
            "message_type": "offer",
            "price": "550.00",
            "content": "I can do it for ₹550",
        }
        form = NegotiationMessageForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_negotiation_message_form_offer_without_price(self):
        """Test negotiation message form offer type without price"""
        form_data = {"message_type": "offer", "content": "I can do it for less"}
        form = NegotiationMessageForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

    def test_negotiation_message_form_counter_without_price(self):
        """Test negotiation message form counter type without price"""
        form_data = {"message_type": "counter", "content": "How about ₹500?"}
        form = NegotiationMessageForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)
