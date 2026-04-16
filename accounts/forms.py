from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
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
)

SKILL_CHOICES = [
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


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["name", "email", "role", "location", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Full Name"}
        )
        self.fields["email"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Email"}
        )
        self.fields["role"].widget.attrs.update({"class": "form-control"})
        self.fields["location"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Location"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Confirm Password"}
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email.split("@")[0]
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Email"}
        )


class JobForm(forms.ModelForm):
    TIME_SLOT_CHOICES = [
        ("morning", "Morning (6:00 AM - 12:00 PM)"),
        ("afternoon", "Afternoon (12:00 PM - 6:00 PM)"),
        ("evening", "Evening (6:00 PM - 10:00 PM)"),
        ("full_day", "Full Day"),
    ]

    LOCATION_CHOICES = [
        ("", "Select location"),
        ("Sion", "Sion"),
        ("Wadala", "Wadala"),
        ("Kurla", "Kurla"),
        ("Chembur", "Chembur"),
        ("Parel", "Parel"),
        ("Dadar", "Dadar"),
        ("Govandi", "Govandi"),
    ]

    location = forms.ChoiceField(
        choices=LOCATION_CHOICES, widget=forms.Select(attrs={"class": "form-control"})
    )
    time_slot = forms.ChoiceField(
        choices=TIME_SLOT_CHOICES, widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = Job
        fields = [
            "category",
            "exact_location",
            "location",
            "date",
            "time_slot",
            "image",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].widget.attrs.update({"class": "form-control"})
        self.fields["exact_location"].widget.attrs.update(
            {
                "class": "form-control",
                "rows": 2,
                "placeholder": "Enter exact address (e.g., Building name, Flat number, Landmark)",
            }
        )
        self.fields["image"].widget.attrs.update(
            {"class": "form-control", "accept": "image/*"}
        )
        self.fields["date"].widget.attrs.update(
            {"class": "form-control", "type": "date"}
        )

    def clean_date(self):
        from django.utils import timezone

        date = self.cleaned_data.get("date")
        if date and date < timezone.now().date():
            raise forms.ValidationError("Job date must be in the future.")
        return date


class WorkerProfileForm(forms.ModelForm):
    LOCATION_CHOICES = [
        ("", "Select location"),
        ("Sion", "Sion"),
        ("Wadala", "Wadala"),
        ("Kurla", "Kurla"),
        ("Chembur", "Chembur"),
        ("Parel", "Parel"),
        ("Dadar", "Dadar"),
        ("Govandi", "Govandi"),
    ]

    location = forms.ChoiceField(
        choices=LOCATION_CHOICES, widget=forms.Select(attrs={"class": "form-control"})
    )

    class Meta:
        model = WorkerProfile
        fields = ["skills", "experience", "base_price", "location"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["skills"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Select skills"}
        )
        self.fields["experience"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Years of experience"}
        )
        self.fields["base_price"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Base price per job"}
        )
        if "location" not in self.fields:
            self.fields["location"] = forms.ChoiceField(
                choices=self.LOCATION_CHOICES,
                widget=forms.Select(attrs={"class": "form-control"}),
            )

    def clean_skills(self):
        skills = self.cleaned_data.get("skills")
        if isinstance(skills, (list, tuple)):
            return ",".join(str(s) for s in skills)
        return str(skills)


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ["date", "time_slot"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].widget.attrs.update(
            {
                "class": "form-control datetimepicker-input",
                "id": "id_date",
                "type": "text",
                "data-target": "#id_date",
                "autocomplete": "off",
            }
        )
        self.fields["time_slot"].widget.attrs.update({"class": "form-control"})


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ["offered_price", "message"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["offered_price"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Enter your price"}
        )
        self.fields["message"].widget.attrs.update(
            {
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional message to customer",
            }
        )


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rating"].widget.attrs.update({"class": "form-control"})
        self.fields["comment"].widget.attrs.update(
            {
                "class": "form-control",
                "rows": 3,
                "placeholder": "Share your experience...",
            }
        )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "profile_photo",
            "phone_number",
            "address",
            "date_of_birth",
            "gender",
            "bio",
            "emergency_contact",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profile_photo"].widget.attrs.update(
            {"class": "form-control", "accept": "image/*"}
        )
        self.fields["phone_number"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Phone number"}
        )
        self.fields["address"].widget.attrs.update(
            {"class": "form-control", "rows": 2, "placeholder": "Address"}
        )
        self.fields["date_of_birth"].widget.attrs.update(
            {"class": "form-control", "type": "date"}
        )
        self.fields["gender"].widget.attrs.update({"class": "form-control"})
        self.fields["bio"].widget.attrs.update(
            {
                "class": "form-control",
                "rows": 3,
                "placeholder": "Tell us about yourself...",
            }
        )
        self.fields["emergency_contact"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Emergency contact number"}
        )


class NegotiationForm(forms.ModelForm):
    class Meta:
        model = Negotiation
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class NegotiationMessageForm(forms.ModelForm):
    MESSAGE_TYPE_CHOICES = [
        ("offer", "New Offer"),
        ("counter", "Counter Offer"),
        ("text", "Message"),
        ("accept", "Accept"),
        ("reject", "Reject"),
    ]

    message_type = forms.ChoiceField(
        choices=MESSAGE_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = NegotiationMessage
        fields = ["message_type", "price", "content"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Enter price (₹)"}
        )
        self.fields["content"].widget.attrs.update(
            {
                "class": "form-control",
                "rows": 2,
                "placeholder": "Your message or counter offer...",
            }
        )

    def clean_price(self):
        message_type = self.cleaned_data.get("message_type")
        price = self.cleaned_data.get("price")
        if message_type in ["counter", "offer"] and not price:
            raise forms.ValidationError(
                "Price is required for offers and counter offers."
            )
        return price
