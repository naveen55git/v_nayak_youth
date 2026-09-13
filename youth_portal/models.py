import random
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    surname = models.CharField(max_length=100, verbose_name="Surname", blank=True, default="")
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        verbose_name="Phone Number",
        help_text="10-digit mobile number"
    )
    email = models.EmailField(unique=True, verbose_name="Registered Gmail")
    caste = models.CharField(max_length=100, blank=True, default="", verbose_name="Caste / Category")
    aadhaar_number = models.CharField(max_length=20, blank=True, default="", verbose_name="Aadhaar Number")
    address = models.TextField(blank=True, default="", verbose_name="Local Residential Address")
    photo = models.ImageField(upload_to='member_photos/', blank=True, null=True, verbose_name="Passport Photo")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Profile Avatar")
    membership_id = models.CharField(max_length=30, unique=True, blank=True, null=True, verbose_name="Membership ID")
    tenure = models.CharField(max_length=100, default="2026 - 2032 (6 Years Official Term)", verbose_name="Membership Tenure")
    is_membership_active = models.BooleanField(default=False, verbose_name="Membership Active")

    def __str__(self):
        return f"{self.username} ({self.get_full_name_custom()})"

    def get_full_name_custom(self):
        full = f"{self.surname} {self.last_name}".strip()
        return full if full else self.username

    def generate_membership_id(self):
        if not self.membership_id:
            while True:
                suffix = random.randint(1000, 9999)
                new_id = f"VNYA-2026-{suffix}"
                if not User.objects.filter(membership_id=new_id).exists():
                    self.membership_id = new_id
                    break
        return self.membership_id


class EmailOTP(models.Model):
    email = models.EmailField(verbose_name="Registered Email Address")
    otp_code = models.CharField(max_length=6, verbose_name="OTP Code")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Email OTP for {self.email}: {self.otp_code} (Used: {self.is_used})"

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at


# Alias for backwards compatibility
MobileOTP = EmailOTP



class CommunityFeature(models.Model):
    title = models.CharField(max_length=200, verbose_name="Feature Title")
    badge = models.CharField(max_length=50, default="ANNOUNCEMENT", verbose_name="Badge Tag")
    description = models.TextField(verbose_name="Feature Description")
    link = models.URLField(blank=True, default="", verbose_name="External Link / URL")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.badge}] {self.title}"


class GalleryImage(models.Model):
    title = models.CharField(max_length=200, verbose_name="Title / Caption")
    image = models.ImageField(upload_to='gallery/', verbose_name="Photo File")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Festival(models.Model):
    name = models.CharField(max_length=200, verbose_name="Festival Name")
    date_text = models.CharField(max_length=100, verbose_name="Festival Date / Month")
    description = models.TextField(verbose_name="Details & Significance")
    image = models.ImageField(upload_to='festivals/', blank=True, null=True, verbose_name="Festival Poster")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.date_text})"


class Sponsorship(models.Model):
    name = models.CharField(max_length=150, verbose_name="Sponsor Full Name")
    phone = models.CharField(max_length=15, verbose_name="Phone Number")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Amount Sent (₹)")
    screenshot = models.ImageField(upload_to='sponsor_receipts/', blank=True, null=True, verbose_name="Payment Screenshot")
    message = models.CharField(max_length=250, blank=True, default="", verbose_name="Purpose / Message")
    is_verified = models.BooleanField(default=True, verbose_name="Verified Receipt")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - ₹{self.amount}"


class Complaint(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('IN_PROGRESS', 'Under Investigation'),
        ('RESOLVED', 'Resolved'),
    ]

    name_or_id = models.CharField(max_length=150, verbose_name="Name or User ID")
    phone = models.CharField(max_length=15, verbose_name="Contact Phone")
    subject = models.CharField(max_length=200, verbose_name="Complaint Subject")
    description = models.TextField(verbose_name="Detailed Grievance")
    image = models.ImageField(upload_to='complaints/', blank=True, null=True, verbose_name="Attached Photo")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    admin_notes = models.TextField(blank=True, default="", verbose_name="Admin Remarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.status}] {self.subject} by {self.name_or_id}"
