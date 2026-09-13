import random
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from .models import MobileOTP

logger = logging.getLogger(__name__)


def clean_phone_number(phone):
    """Normalize phone number to digits only (e.g., 10 digits)."""
    digits = ''.join(c for c in str(phone) if c.isdigit())
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def generate_and_send_otp(phone_number, request=None):
    """
    Generate a 6-digit OTP, persist it in the database with a 5-minute expiry,
    print it to the server console, and optionally store in request.session for dev toast.
    """
    phone = clean_phone_number(phone_number)
    otp_code = f"{random.randint(100000, 999999)}"
    expires_at = timezone.now() + timedelta(minutes=5)

    # Invalidate previous unused OTPs for this phone
    MobileOTP.objects.filter(phone_number=phone, is_used=False).update(is_used=True)

    # Create new OTP record
    otp_record = MobileOTP.objects.create(
        phone_number=phone,
        otp_code=otp_code,
        expires_at=expires_at,
        is_used=False
    )

    # Output clearly in server console
    print("\n" + "=" * 60)
    print(f" [V.NAYAK YOUTH MADHARAM] SMS OTP DISPATCH")
    print(f" Mobile Number : +91 {phone}")
    print(f" OTP Code      : {otp_code}")
    print(f" Valid Until   : {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')} (5 mins)")
    print("=" * 60 + "\n")

    logger.info(f"Generated OTP for {phone}: {otp_code}")

    # Store in session for easy testing in development environment
    if request is not None and getattr(settings, 'DEBUG', True):
        request.session['dev_latest_otp'] = otp_code
        request.session['dev_otp_phone'] = phone

    # Pluggable SMS Gateway hook (e.g. Twilio / Fast2SMS) can be called here
    # Example: send_via_third_party_gateway(phone, otp_code)

    return otp_code


def verify_mobile_otp(phone_number, entered_otp):
    """
    Verify the submitted OTP against the latest active OTP record in SQLite.
    Marks OTP as used upon successful verification.
    """
    phone = clean_phone_number(phone_number)
    entered_otp = str(entered_otp).strip()

    otp_record = MobileOTP.objects.filter(
        phone_number=phone,
        is_used=False
    ).order_by('-created_at').first()

    if not otp_record:
        return False, "No OTP request found for this mobile number. Please request a new OTP."

    if not otp_record.is_valid():
        return False, "OTP has expired. Please request a new OTP."

    if otp_record.otp_code != entered_otp:
        return False, "Invalid OTP code. Please enter the correct 6-digit code."

    # Mark as used
    otp_record.is_used = True
    otp_record.save(update_fields=['is_used'])

    return True, "OTP verified successfully."
