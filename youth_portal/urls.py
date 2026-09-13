from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('festivals/', views.festivals_view, name='festivals'),
    path('sponsor/', views.sponsor_view, name='sponsor'),
    path('complaints/', views.complaint_view, name='complaints'),
    path('profile/', views.profile_view, name='profile'),
    path('register/', views.register_view, name='register'),
    path('login/', views.request_otp_view, name='login_otp'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('membership/apply/', views.membership_view, name='membership_apply'),
    path('membership/card/', views.membership_card_view, name='membership_card'),
    path('secretariat-admin/', views.admin_panel_view, name='admin_panel'),
    path('logout/', views.logout_view, name='logout'),
]
