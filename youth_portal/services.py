import json
import logging
import secrets
import urllib.parse
import urllib.request
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from .models import MobileOTP, User

logger = logging.getLogger(__name__)


def clean_phone_number(phone):
    """Normalize phone number to 10 digits."""
    digits = ''.join(c for c in str(phone) if c.isdigit())
    if len(digits) > 10:
        digits = digits[-10:]
    return digits


def mask_phone_number(phone):
    """Return a masked representation of the phone number for secure display, e.g., +91 ******4977."""
    cleaned = clean_phone_number(phone)
    if len(cleaned) == 10:
        return f"+91 ******{cleaned[-4:]}"
    return f"+91 {cleaned}"


def can_resend_otp(phone_number, cooldown_seconds=30):
    """Check if the user can request a new OTP or must wait for the cooldown."""
    phone = clean_phone_number(phone_number)
    recent = MobileOTP.objects.filter(phone_number=phone).order_by('-created_at').first()
    if recent:
        elapsed = (timezone.now() - recent.created_at).total_seconds()
        if elapsed < cooldown_seconds:
            remaining = int(cooldown_seconds - elapsed)
            return False, remaining
    return True, 0


def send_fast2sms(phone, otp_code):
    """
    Send real SMS via Fast2SMS Indian OTP Route.
    Fast2SMS provides instant DLT-approved OTP delivery across India (+91).
    """
    api_key = getattr(settings, 'FAST2SMS_API_KEY', '')
    if not api_key:
        return False, "FAST2SMS_API_KEY not configured"

    url = "https://www.fast2sms.com/dev/bulkV2"
    payload = {
        "route": "otp",
        "variables_values": otp_code,
        "numbers": phone,
        "flash": "0"
    }
    headers = {
        "authorization": api_key,
        "Content-Type": "application/json"
    }

    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            res = json.loads(body)
            if res.get('return'):
                logger.info(f"Fast2SMS delivered OTP to {phone}: {res.get('message')}")
                return True, "SMS sent successfully via Fast2SMS"
            else:
                logger.warning(f"Fast2SMS returned error for {phone}: {res.get('message')}")
                return False, res.get('message', 'SMS gateway error')
    except Exception as e:
        logger.error(f"Fast2SMS dispatch failed for {phone}: {e}")
        return False, str(e)


def send_twilio_sms(phone, otp_code):
    """Send real SMS via Twilio API."""
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', '')

    if not (account_sid and auth_token and from_number):
        return False, "Twilio credentials not configured"

    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    payload = urllib.parse.urlencode({
        "To": f"+91{phone}",
        "From": from_number,
        "Body": f"Your V.NAYAK YOUTH ASSOCIATION verification code is {otp_code}. Valid for 5 minutes. Do not share this code."
    }).encode('utf-8')

    import base64
    auth_str = f"{account_sid}:{auth_token}"
    b64_auth = base64.b64encode(auth_str.encode('ascii')).decode('ascii')

    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201):
                logger.info(f"Twilio SMS sent to +91{phone}")
                return True, "SMS sent successfully via Twilio"
    except Exception as e:
        logger.error(f"Twilio dispatch failed for +91{phone}: {e}")
        return False, str(e)

    return False, "Twilio request failed"


def send_twofactor_sms(phone, otp_code):
    """Send real SMS via 2Factor.in gateway."""
    api_key = getattr(settings, 'TWOFACTOR_API_KEY', '')
    if not api_key:
        return False, "2Factor API key not configured"

    url = f"https://2factor.in/API/V1/{api_key}/SMS/{phone}/{otp_code}/AUTOGEN"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode('utf-8')
            res = json.loads(body)
            if res.get('Status') == 'Success':
                logger.info(f"2Factor SMS sent to {phone}")
                return True, "SMS sent successfully via 2Factor"
    except Exception as e:
        logger.error(f"2Factor dispatch failed for {phone}: {e}")
        return False, str(e)

    return False, "2Factor failed"


def send_email_otp(email_address, otp_code, user_name="Member"):
    """Send real OTP notification to user's registered email."""
    if not email_address:
        return False, "No email address provided"

    subject = f"V.NAYAK YOUTH ASSOCIATION - Your Login OTP: {otp_code}"
    message = (
        f"Namaste {user_name},\n\n"
        f"Your one-time verification code (OTP) for V.NAYAK YOUTH ASSOCIATION is:\n\n"
        f"       >>>  {otp_code}  <<<\n\n"
        f"This code is confidential and is valid for 5 minutes.\n"
        f"Please do not share this OTP with anyone.\n\n"
        f"Best Regards,\n"
        f"V.NAYAK YOUTH ASSOCIATION\n"
        f"Madharam Village, Singareni Mandal, Khammam District, Telangana 507122\n"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'V.NAYAK YOUTH <noreply@vnayakyouth.org>'),
            recipient_list=[email_address],
            fail_silently=True
        )
        logger.info(f"Dispatched email OTP to {email_address}")
        return True, f"Email OTP sent to {email_address}"
    except Exception as e:
        logger.error(f"Email dispatch error for {email_address}: {e}")
        return False, str(e)


def generate_and_send_otp(phone_number, request=None, email=None):
    """
    Generate a cryptographically secure 6-digit OTP, persist it in SQLite with 5-minute expiry,
    and dispatch via real SMS / Email channels.
    NEVER leaks OTP code to session or frontend templates.
    """
    phone = clean_phone_number(phone_number)
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = timezone.now() + timedelta(minutes=5)

    # Invalidate any previous unused OTPs for this phone
    MobileOTP.objects.filter(phone_number=phone, is_used=False).update(is_used=True)

    # Persist the new OTP record securely
    MobileOTP.objects.create(
        phone_number=phone,
        otp_code=otp_code,
        expires_at=expires_at,
        is_used=False
    )

    logger.info(f"Secure OTP generated for phone ending in ...{phone[-4:]}")

    # Dispatch via Real Channels
    dispatched_sms = False
    delivery_note = []

    # 1. Fast2SMS (Indian Gateway)
    success, msg = send_fast2sms(phone, otp_code)
    if success:
        dispatched_sms = True
        delivery_note.append("Fast2SMS")
    else:
        # 2. Twilio Gateway Fallback
        t_success, t_msg = send_twilio_sms(phone, otp_code)
        if t_success:
            dispatched_sms = True
            delivery_note.append("Twilio")
        else:
            # 3. 2Factor Gateway Fallback
            tf_success, tf_msg = send_twofactor_sms(phone, otp_code)
            if tf_success:
                dispatched_sms = True
                delivery_note.append("2Factor")

    # 4. Email OTP Dispatch (Companion / Fallback)
    target_email = email
    user_name = "Member"
    if not target_email:
        user = User.objects.filter(phone_number=phone).first()
        if user and user.email:
            target_email = user.email
            user_name = user.get_full_name_custom()

    if target_email:
        send_email_otp(target_email, otp_code, user_name)
        delivery_note.append(f"Email ({target_email})")

    if not dispatched_sms:
        # Log to server console so administrators can verify during testing or when SMS gateway balance is low
        print("\n" + "=" * 65)
        print(" [V.NAYAK YOUTH MADHARAM] REAL OTP DISPATCH LOG")
        print(f" Mobile Number : +91 {phone} (Masked: {mask_phone_number(phone)})")
        print(f" OTP Code      : {otp_code}")
        print(f" Valid Until   : {expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')} (5 minutes)")
        print(f" SMS Gateways  : {'Sent via ' + ', '.join(delivery_note) if delivery_note else 'Pending Gateway API Key'}")
        print("=" * 65 + "\n")

    return otp_code


def verify_mobile_otp(phone_number, entered_otp):
    """
    Verify the submitted OTP against the latest active record in SQLite.
    Marks OTP as used upon successful verification.
    """
    phone = clean_phone_number(phone_number)
    entered_otp = str(entered_otp).strip()

    otp_record = MobileOTP.objects.filter(
        phone_number=phone,
        is_used=False
    ).order_by('-created_at').first()

    if not otp_record:
        return False, "No active OTP request found for this mobile number. Please request a new OTP."

    if not otp_record.is_valid():
        return False, "The OTP has expired (5-minute limit). Please click Resend OTP."

    if otp_record.otp_code != entered_otp:
        return False, "Invalid OTP verification code. Please check and try again."

    # Mark as used immediately to prevent replay attacks
    otp_record.is_used = True
    otp_record.save(update_fields=['is_used'])

    return True, "OTP verified successfully."

