from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
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

# Customize admin site
admin.site.site_header = "LocalKaam Control Center"
admin.site.site_title = "LocalKaam Admin"
admin.site.index_title = "Welcome to LocalKaam Administration"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email",
        "name",
        "role_badge",
        "verification_badge",
        "status_badge",
        "date_joined",
    ]
    list_filter = ["role", "is_active", "is_email_verified", "is_staff"]
    search_fields = ["email", "name"]
    ordering = ["-date_joined"]

    def role_badge(self, obj):
        colors = {"customer": "#3b82f6", "worker": "#8b5cf6", "admin": "#ef4444"}
        color = colors.get(obj.role, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_role_display().upper(),
        )

    role_badge.short_description = "Role"

    def verification_badge(self, obj):
        if obj.is_email_verified:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600;">✓ VERIFIED</span>'
            )
        return format_html(
            '<span style="background-color: #ef4444; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600;">✗ UNVERIFIED</span>'
        )

    verification_badge.short_description = "Email Status"

    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #06b6d4; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600;">● ACTIVE</span>'
            )
        return format_html(
            '<span style="background-color: #6b7280; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600;">● INACTIVE</span>'
        )

    status_badge.short_description = "Status"

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
        "status_badge",
        "date",
        "location",
        "created_at",
    ]
    list_filter = ["status", "category", "date"]
    search_fields = ["category", "location", "customer__name", "worker__name"]
    readonly_fields = ["created_at", "updated_at"]

    def status_badge(self, obj):
        status_colors = {
            "pending": "#f59e0b",
            "accepted": "#3b82f6",
            "completed": "#10b981",
            "cancelled": "#ef4444",
        }
        color = status_colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display().upper(),
        )

    status_badge.short_description = "Status"


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
    list_display = [
        "id",
        "job",
        "worker",
        "offered_price",
        "status_badge",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["worker__name", "job__category"]
    readonly_fields = ["created_at", "updated_at"]

    def status_badge(self, obj):
        status_colors = {
            "pending": "#f59e0b",
            "accepted": "#10b981",
            "rejected": "#ef4444",
        }
        color = status_colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display().upper(),
        )

    status_badge.short_description = "Status"


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
        "status_badge",
        "created_at",
    ]
    list_filter = ["status", "created_at"]
    search_fields = ["worker__name", "customer__name", "job__category"]
    readonly_fields = ["created_at", "updated_at"]

    def status_badge(self, obj):
        status_colors = {
            "pending": "#f59e0b",
            "accepted": "#10b981",
            "rejected": "#ef4444",
            "in_progress": "#3b82f6",
        }
        color = status_colors.get(obj.status, "#6b7280")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display().upper(),
        )

    status_badge.short_description = "Status"


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
