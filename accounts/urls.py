from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.resend_verification, name='resend_verification'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('reset-password/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('customer/dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('customer/create-job/', views.create_job, name='create_job'),
    path('customer/job/<int:job_id>/edit/', views.edit_job, name='edit_job'),
    path('customer/job/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    path('customer/job/<int:job_id>/quotations/', views.view_quotations, name='view_quotations'),
    path('customer/quotation/<int:quotation_id>/accept/', views.accept_quotation, name='accept_quotation'),
    path('customer/quotation/<int:quotation_id>/reject/', views.reject_quotation, name='reject_quotation'),
    path('worker/dashboard/', views.worker_dashboard, name='worker_dashboard'),
    path('worker/profile/', views.worker_profile, name='worker_profile'),
    path('worker/availability/', views.manage_availability, name='manage_availability'),
    path('worker/availability/delete/<int:availability_id>/', views.delete_availability, name='delete_availability'),
    path('worker/job/<int:job_id>/quotation/', views.submit_quotation, name='submit_quotation'),
    path('worker/job/<int:job_id>/complete/', views.mark_job_completed, name='mark_job_completed'),
    path('customer/job/<int:job_id>/review/', views.create_review, name='create_review'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    path('customer/quotation/<int:quotation_id>/negotiate/', views.start_negotiation, name='start_negotiation'),
    path('customer/negotiations/', views.customer_negotiations, name='customer_negotiations'),
    path('worker/negotiations/', views.worker_negotiations, name='worker_negotiations'),
    path('worker/job/<int:job_id>/negotiate/', views.worker_start_negotiation, name='worker_start_negotiation'),
    path('negotiation/<int:negotiation_id>/', views.negotiation_detail, name='negotiation_detail'),
]
