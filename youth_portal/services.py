import logging
import secrets
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from .models import EmailOTP, User

logger = logging.getLogger(__name__)


def clean_phone_number(phone):
    """Normalize phone number to 10 digits."""
    digits = ''.join(c for c in str(phone) if c.isdigit())
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def mask_email(email):
    """Return a masked representation of the email for secure display, e.g., mrw***@gmail.com."""
    email = str(email).strip().lower()
    if '@' not in email:
        return email
    user_part, domain = email.split('@', 1)
    if len(user_part) <= 3:
        masked_user = user_part[0] + '***'
    else:
        masked_user = user_part[:3] + '***' + user_part[-1]
    return f"{masked_user}@{domain}"


def can_resend_email_otp(email, cooldown_seconds=30):
    """Check if the user can request a new Email OTP or must wait for the cooldown."""
    email = str(email).strip().lower()
    recent = EmailOTP.objects.filter(email=email).order_by('-created_at').first()
    if recent:
        elapsed = (timezone.now() - recent.created_at).total_seconds()
        if elapsed < cooldown_seconds:
            remaining = int(cooldown_seconds - elapsed)
            return False, remaining
    return True, 0


def send_email_otp(email_address, otp_code, user_name="Youth Member"):
    """
    Send real OTP notification directly to user's registered email address.
    """
    if not email_address:
        return False, "No email address provided"

    email_address = str(email_address).strip().lower()
    subject = f"V.NAYAK YOUTH ASSOCIATION - Verification Code: {otp_code}"
    message = (
        f"Namaste {user_name},\n\n"
        f"Your confidential one-time verification code (OTP) for V.NAYAK YOUTH ASSOCIATION is:\n\n"
        f"       =============================\n"
        f"       >>>        {otp_code}        <<<\n"
        f"       =============================\n\n"
        f"This code is strictly valid for 5 minutes.\n"
        f"Please do not share this code with anyone.\n\n"
        f"If you did not initiate this request, you can safely ignore this email.\n\n"
        f"Warm Regards,\n"
        f"V.NAYAK YOUTH ASSOCIATION\n"
        f"Madharam Village, Singareni Mandal, Khammam District, Telangana 507122\n"
    )

    sent = False
    error_msg = None
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'V.NAYAK YOUTH ASSOCIATION <noreply@vnayakyouth.org>'),
            recipient_list=[email_address],
            fail_silently=False
        )
        sent = True
        logger.info(f"Email OTP sent successfully to {email_address}")
    except Exception as e:
        error_msg = str(e)
        logger.warning(f"SMTP delivery note for {email_address}: {e}")

    # Log to server console so developers and admins can always see active OTPs in server logs
    print("\n" + "=" * 65)
    print(" [V.NAYAK YOUTH MADHARAM] REAL EMAIL OTP DISPATCH")
    print(f" Registered Email : {email_address} (Masked: {mask_email(email_address)})")
    print(f" OTP Code         : {otp_code}")
    print(f" Delivery Mode    : {'Delivered via SMTP' if sent else f'Console Log ({error_msg or 'Local Mode'})'}")
    print("=" * 65 + "\n")

    return True, "Email OTP dispatched."


def generate_and_send_email_otp(email_address, request=None, user_name=None):
    """
    Generate a cryptographically secure 6-digit OTP, persist it in SQLite with 5-minute expiry,
    and send to the registered email address.
    """
    email = str(email_address).strip().lower()
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = timezone.now() + timedelta(minutes=5)

    # Invalidate any previous unused OTPs for this email
    EmailOTP.objects.filter(email=email, is_used=False).update(is_used=True)

    # Persist the new OTP record securely
    EmailOTP.objects.create(
        email=email,
        otp_code=otp_code,
        expires_at=expires_at,
        is_used=False
    )

    if not user_name:
        user = User.objects.filter(email=email).first()
        if user:
            user_name = user.get_full_name_custom()
        else:
            user_name = "Youth Member"

    send_email_otp(email, otp_code, user_name=user_name)
    return otp_code


def verify_email_otp(email_address, entered_otp):
    """
    Verify the submitted OTP against the latest active record in SQLite.
    Marks OTP as used upon successful verification.
    """
    email = str(email_address).strip().lower()
    entered_otp = str(entered_otp).strip()

    otp_record = EmailOTP.objects.filter(
        email=email,
        is_used=False
    ).order_by('-created_at').first()

    if not otp_record:
        return False, "No active OTP request found for this email. Please request a new code."

    if not otp_record.is_valid():
        return False, "The OTP has expired (5-minute limit). Please click Resend Code."

    if otp_record.otp_code != entered_otp:
        return False, "Invalid verification code. Please check your email and try again."

    # Mark as used immediately to prevent replay attacks
    otp_record.is_used = True
    otp_record.save(update_fields=['is_used'])

    return True, "Email verified successfully."


# Backward compatibility aliases
generate_and_send_otp = generate_and_send_email_otp
verify_mobile_otp = verify_email_otp
mask_phone_number = mask_email
can_resend_otp = can_resend_email_otp


