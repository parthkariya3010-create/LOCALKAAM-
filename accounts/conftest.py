import pytest
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from accounts.models import UserProfile, WorkerProfile, Job, Quotation, Availability
import factory
from faker import Faker

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.LazyAttribute(lambda x: fake.email())
    name = factory.LazyAttribute(lambda x: fake.name())
    username = factory.LazyAttribute(lambda x: fake.user_name())
    role = "customer"
    is_active = True
    is_email_verified = True


class WorkerUserFactory(UserFactory):
    role = "worker"


class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    phone_number = factory.LazyAttribute(lambda x: fake.phone_number()[:10])
    address = factory.LazyAttribute(lambda x: fake.address())


class WorkerProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorkerProfile

    user = factory.SubFactory(WorkerUserFactory)
    skills = "plumbing,electrical"
    experience = 5
    base_price = 500.00
    location = factory.LazyAttribute(lambda x: fake.city())


class JobFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Job

    customer = factory.SubFactory(UserFactory)
    category = "plumbing"
    location = factory.LazyAttribute(lambda x: fake.city())
    date = factory.LazyAttribute(lambda x: fake.date_this_month())
    time_slot = "morning"


class QuotationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Quotation

    job = factory.SubFactory(JobFactory)
    worker = factory.SubFactory(WorkerUserFactory)
    offered_price = 600.00


class AvailabilityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Availability

    worker = factory.SubFactory(WorkerUserFactory)
    date = factory.LazyAttribute(lambda x: fake.date_this_month())
    time_slot = "morning"


@pytest.fixture
def rf():
    """RequestFactory fixture"""
    return RequestFactory()


@pytest.fixture
def user():
    """Basic user fixture"""
    return UserFactory()


@pytest.fixture
def worker_user():
    """Worker user fixture"""
    return WorkerUserFactory()


@pytest.fixture
def customer_user():
    """Customer user fixture"""
    return UserFactory(role="customer")


@pytest.fixture
def job(customer_user):
    """Job fixture"""
    return JobFactory(customer=customer_user)


@pytest.fixture
def worker_profile(worker_user):
    """Worker profile fixture"""
    return WorkerProfileFactory(user=worker_user)


@pytest.fixture
def quotation(job, worker_user):
    """Quotation fixture"""
    return QuotationFactory(job=job, worker=worker_user)
