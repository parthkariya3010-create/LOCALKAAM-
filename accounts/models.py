from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth.hashers import make_password
import uuid
import secrets

class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('worker', 'Worker'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    location = models.CharField(max_length=255, blank=True)
    
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)
    
    password_reset_token = models.CharField(max_length=64, blank=True)
    password_reset_sent_at = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']
    
    def __str__(self):
        return self.email
    
    def generate_email_verification_token(self):
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_sent_at = timezone.now()
        self.save(update_fields=['email_verification_token', 'email_verification_sent_at'])
        return self.email_verification_token
    
    def generate_password_reset_token(self):
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_sent_at = timezone.now()
        self.save(update_fields=['password_reset_token', 'password_reset_sent_at'])
        return self.password_reset_token
    
    def verify_email(self, token):
        if self.email_verification_token == token:
            self.is_email_verified = True
            self.is_active = True
            self.email_verification_token = ''
            self.save(update_fields=['is_email_verified', 'is_active', 'email_verification_token'])
            return True
        return False
    
    def reset_password(self, token, new_password):
        if self.password_reset_token == token:
            if self.password_reset_sent_at:
                if (timezone.now() - self.password_reset_sent_at).seconds < 3600:
                    self.set_password(new_password)
                    self.password_reset_token = ''
                    self.save(update_fields=['password', 'password_reset_token'])
                    return True
        return False


class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_photo = models.ImageField(upload_to='profile_photos/', default='default.png', blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    bio = models.TextField(blank=True, max_length=500)
    emergency_contact = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Profile of {self.user.name}"

class Job(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
    ]
    
    CATEGORY_CHOICES = [
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('cleaning', 'Cleaning'),
        ('painting', 'Painting'),
        ('carpentry', 'Carpentry'),
        ('gardening', 'Gardening'),
        ('moving', 'Moving'),
        ('ac', 'AC Technician'),
        ('appliance', 'Appliance Repair'),
        ('other', 'Other'),
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    worker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_jobs')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    exact_location = models.TextField(default='', help_text="Exact address/location for the job")
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='job_images/', blank=True, null=True, help_text="Upload a photo of the job")
    date = models.DateField()
    time_slot = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.category} - {self.location} - {self.date}"

class WorkerProfile(models.Model):
    SKILL_CHOICES = [
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('cleaning', 'Cleaning'),
        ('painting', 'Painting'),
        ('carpentry', 'Carpentry'),
        ('gardening', 'Gardening'),
        ('moving', 'Moving'),
        ('other', 'Other'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='worker_profile')
    skills = models.CharField(max_length=255, help_text="Comma-separated skills")
    experience = models.IntegerField(help_text="Years of experience")
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base price per job")
    location = models.CharField(max_length=100, blank=True, help_text="Work location")
    avg_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.name} - {self.skills}"
    
    @property
    def skills_list(self):
        return [s.strip() for s in self.skills.split(',') if s.strip()]

class Availability(models.Model):
    TIME_SLOTS = [
        ('morning', 'Morning (6AM - 12PM)'),
        ('afternoon', 'Afternoon (12PM - 6PM)'),
        ('evening', 'Evening (6PM - 10PM)'),
        ('full_day', 'Full Day'),
    ]
    
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    time_slot = models.CharField(max_length=20, choices=TIME_SLOTS)
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['worker', 'date', 'time_slot']
    
    def __str__(self):
        return f"{self.worker.name} - {self.date} - {self.time_slot}"

class Quotation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='quotations')
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='quotations')
    offered_price = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(blank=True, help_text="Optional message from worker")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['job', 'worker']
    
    def __str__(self):
        return f"Quotation by {self.worker.name} for {self.job.category} - ₹{self.offered_price}"

class Review(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='review')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_reviews')
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reviews')
    rating = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Review by {self.customer.name} for {self.worker.name} - {self.rating}★"


class Negotiation(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='negotiations')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='negotiations')
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='negotiations_initiated')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='negotiations_received')
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['quotation', 'worker']
    
    def __str__(self):
        return f"Negotiation for {self.job.category} - ₹{self.current_price}"
    
    @property
    def messages_list(self):
        return self.messages.all().order_by('created_at')


class NegotiationMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('offer', 'Initial Offer'),
        ('counter', 'Counter Offer'),
        ('accept', 'Accepted'),
        ('reject', 'Rejected'),
        ('text', 'Message'),
    ]
    
    negotiation = models.ForeignKey(Negotiation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='negotiation_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Message by {self.sender.name} - {self.message_type}"
