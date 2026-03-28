from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
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


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email",
        "name",
        "role",
        "is_email_verified",
        "is_active",
        "date_joined",
    ]
    list_filter = ["role", "is_active", "is_email_verified", "is_staff"]
    search_fields = ["email", "name"]
    ordering = ["-date_joined"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("role", "location", "is_email_verified")}),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "phone_number", "gender", "created_at"]
    search_fields = ["user__name", "user__email", "phone_number"]
    list_filter = ["gender"]


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "category",
        "customer",
        "worker",
        "status",
        "date",
        "location",
        "created_at",
    ]
    list_filter = ["status", "category", "date"]
    search_fields = ["category", "location", "customer__name", "worker__name"]
    list_editable = ["status"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "skills",
        "experience",
        "base_price",
        "location",
        "avg_rating",
        "created_at",
    ]
    list_filter = ["skills"]
    search_fields = ["user__name", "skills", "location"]
    readonly_fields = ["created_at", "updated_at", "avg_rating"]


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ["worker", "date", "time_slot", "is_available"]
    list_filter = ["date", "is_available", "time_slot"]
    search_fields = ["worker__name"]


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ["id", "job", "worker", "offered_price", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["worker__name", "job__category"]
    list_editable = ["status"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "worker", "rating", "job", "created_at"]
    list_filter = ["rating"]
    search_fields = ["customer__name", "worker__name", "comment"]
    readonly_fields = ["created_at"]


@admin.register(Negotiation)
class NegotiationAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "job",
        "worker",
        "customer",
        "current_price",
        "status",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["worker__name", "customer__name", "job__category"]
    list_editable = ["status"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["customer", "worker", "created_at"]
    search_fields = ["customer__name", "worker__name"]


@admin.register(NegotiationMessage)
class NegotiationMessageAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "negotiation",
        "sender",
        "message_type",
        "price",
        "created_at",
    ]
    list_filter = ["message_type"]
    search_fields = ["sender__name", "content"]
    readonly_fields = ["created_at"]
