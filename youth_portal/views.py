from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.db.models import Sum
from .models import User, CommunityFeature, GalleryImage, Festival, Sponsorship, Complaint
from .forms import (
    YouthRegistrationForm,
    EmailRequestOTPForm,
    VerifyOTPForm,
    MembershipDetailsForm,
    UserProfileForm,
    SponsorshipForm,
    ComplaintForm,
    CommunityFeatureForm,
    GalleryImageForm,
    FestivalForm
)
from .services import (
    generate_and_send_email_otp,
    verify_email_otp,
    mask_email,
    can_resend_email_otp
)



def home_view(request):
    """
    Combined home landing page featuring hero banner, live updates & upcoming features,
    statistics, mandate pillars, quick action modules, and quick mobile OTP login card.
    """
    total_members = User.objects.count()
    active_cards = User.objects.filter(is_membership_active=True).count()
    total_sponsorship = Sponsorship.objects.filter(is_verified=True).aggregate(Sum('amount'))['amount__sum'] or 0
    features = CommunityFeature.objects.all()[:6]
    festivals = Festival.objects.all()[:3]

    reg_form = YouthRegistrationForm()
    login_form = EmailRequestOTPForm()


    context = {
        'total_members': total_members,
        'active_cards': active_cards,
        'total_sponsorship': total_sponsorship,
        'features': features,
        'festivals': festivals,
        'reg_form': reg_form,
        'login_form': login_form,
    }
    return render(request, 'youth_portal/home.html', context)


def gallery_view(request):
    """Photo gallery of youth sports, tournaments, and social community work."""
    if request.method == 'POST':
        form = GalleryImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Image uploaded to the community gallery successfully!")
            return redirect('gallery')
        else:
            messages.error(request, "Please choose a valid image file.")
    else:
        form = GalleryImageForm()

    images = GalleryImage.objects.all()
    return render(request, 'youth_portal/gallery.html', {'images': images, 'form': form})


def festivals_view(request):
    """Village festivals, culture, and event guidelines."""
    if request.method == 'POST':
        form = FestivalForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Festival celebration details added successfully!")
            return redirect('festivals')
        else:
            messages.error(request, "Please enter complete festival information.")
    else:
        form = FestivalForm()

    festivals = Festival.objects.all()
    return render(request, 'youth_portal/festivals.html', {'festivals': festivals, 'form': form})


def sponsor_view(request):
    """
    Sponsorship and donation page with payment info to Mood bhanu Prasad (91008 94417),
    UPI QR code, receipt submission, and community honor roll.
    """
    if request.method == 'POST':
        form = SponsorshipForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Thank you for your generous contribution! Your receipt has been submitted for verified honor roll recognition."
            )
            return redirect('sponsor')
        else:
            messages.error(request, "Please fill in all required fields and upload your receipt screenshot.")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'name': request.user.get_full_name_custom(),
                'phone': request.user.phone_number
            }
        form = SponsorshipForm(initial=initial)

    sponsors = Sponsorship.objects.filter(is_verified=True)
    total_raised = sponsors.aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'youth_portal/sponsor.html', {
        'form': form,
        'sponsors': sponsors,
        'total_raised': total_raised
    })


def complaint_view(request):
    """Lodge youth complaints and view recent community grievance updates."""
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save()
            messages.success(
                request,
                f"Your grievance (Ref #{complaint.id}) has been lodged with the Madharam Youth Secretariat. The committee will review it shortly."
            )
            return redirect('complaints')
        else:
            messages.error(request, "Please complete the grievance form.")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'name_or_id': f"{request.user.get_full_name_custom()} (@{request.user.username})",
                'phone': request.user.phone_number
            }
        form = ComplaintForm(initial=initial)

    complaints = Complaint.objects.all()
    return render(request, 'youth_portal/complaints.html', {
        'form': form,
        'complaints': complaints
    })


@login_required
def profile_view(request):
    """Member profile page to update personal details and profile avatar."""
    user = request.user
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile details have been updated successfully!")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors in the profile form.")
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'youth_portal/profile.html', {'form': form, 'user': user})


def register_view(request):
    """Handle new youth member registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = YouthRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Registration successful for {user.get_full_name_custom()}! "
                f"A 6-digit verification code has been dispatched to {mask_email(user.email)}."
            )
            email = user.email
            generate_and_send_email_otp(email, request, user_name=user.get_full_name_custom())
            request.session['auth_email'] = email
            return redirect('verify_otp')
        else:
            messages.error(request, "Please correct the errors in the registration form.")
    else:
        form = YouthRegistrationForm()

    return render(request, 'youth_portal/register.html', {'form': form})


def request_otp_view(request):
    """Request a 6-digit OTP sent to registered email address for secure login."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = EmailRequestOTPForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()
            user_name = user.get_full_name_custom() if user else "Youth Member"
            generate_and_send_email_otp(email, request, user_name=user_name)
            request.session['auth_email'] = email
            messages.info(
                request,
                f"A 6-digit verification code has been sent to {mask_email(email)}."
            )
            return redirect('verify_otp')
        else:
            messages.error(request, "Please enter a valid registered email address.")
    else:
        form = EmailRequestOTPForm()

    return render(request, 'youth_portal/login_otp.html', {'form': form})


def resend_otp_view(request):
    """Resend a fresh OTP to the pending session email address with cooldown rate limiting."""
    email = request.session.get('auth_email')
    if not email:
        messages.warning(request, "Please enter your email address first.")
        return redirect('login_otp')

    allowed, remaining = can_resend_email_otp(email, cooldown_seconds=30)
    if not allowed:
        messages.warning(request, f"Please wait {remaining} seconds before requesting another code.")
        return redirect('verify_otp')

    user = User.objects.filter(email=email).first()
    user_name = user.get_full_name_custom() if user else "Youth Member"
    generate_and_send_email_otp(email, request, user_name=user_name)
    messages.success(request, f"A fresh verification code has been sent to {mask_email(email)}.")
    return redirect('verify_otp')


def verify_otp_view(request):
    """Verify submitted 6-digit OTP code and authenticate user session."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    email = request.session.get('auth_email')
    if not email:
        messages.warning(request, "Session expired or no email specified. Please enter your email.")
        return redirect('login_otp')

    user = User.objects.filter(email=email).first()
    if not user:
        messages.error(request, "No registered account matches this email address.")
        return redirect('login_otp')

    if request.method == 'POST':
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp_code']
            success, msg = verify_email_otp(email, entered_otp)
            if success:
                login(request, user)
                request.session.pop('auth_email', None)
                messages.success(request, f"Welcome back, {user.get_full_name_custom()}! You are now logged in.")
                return redirect('dashboard')
            else:
                messages.error(request, msg)
    else:
        form = VerifyOTPForm()

    context = {
        'form': form,
        'email': email,
        'masked_email': mask_email(email),
    }
    return render(request, 'youth_portal/verify_otp.html', context)




@login_required
def dashboard_view(request):
    """Member profile dashboard displaying youth bulletins and card status."""
    return render(request, 'youth_portal/dashboard.html', {
        'user': request.user,
    })


@login_required
def membership_view(request):
    """Form to submit / update details and upload passport photo for PVC card."""
    user = request.user
    if request.method == 'POST':
        form = MembershipDetailsForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            updated_user = form.save(commit=False)
            updated_user.is_membership_active = True
            updated_user.generate_membership_id()
            updated_user.save()
            messages.success(
                request,
                "Your membership details have been saved and your official 6-Year PVC Card is generated!"
            )
            return redirect('membership_card')
        else:
            messages.error(request, "Please resolve the validation errors below.")
    else:
        initial = {
            'surname': user.surname,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'email': user.email,
            'caste': user.caste or 'ST (Lambada)',
            'address': user.address or 'ST-Colony, Madharam Village, Singareni MLD, Khammam Dist.',
            'aadhaar_number': user.aadhaar_number,
            'tenure': user.tenure
        }
        form = MembershipDetailsForm(instance=user, initial=initial)

    return render(request, 'youth_portal/membership_form.html', {
        'form': form,
        'user': user,
    })


@login_required
def membership_card_view(request):
    """Displays the two-sided PVC membership card with barcode, authorized signature, print, and download."""
    user = request.user
    if not user.membership_id:
        user.generate_membership_id()
        user.is_membership_active = True
        user.save()

    return render(request, 'youth_portal/membership_card.html', {
        'user': user,
    })


@user_passes_test(lambda u: u.is_staff or u.is_superuser, login_url='login_otp')
def admin_panel_view(request):
    """Secretariat Admin Panel for managing features, reviewing grievances, and verifying sponsors."""
    if request.method == 'POST' and 'add_feature' in request.POST:
        feat_form = CommunityFeatureForm(request.POST)
        if feat_form.is_valid():
            feat_form.save()
            messages.success(request, "New announcement published to the home page!")
            return redirect('admin_panel')
    else:
        feat_form = CommunityFeatureForm()

    complaints = Complaint.objects.all()
    sponsors = Sponsorship.objects.all()
    features = CommunityFeature.objects.all()

    return render(request, 'youth_portal/admin_panel.html', {
        'feat_form': feat_form,
        'complaints': complaints,
        'sponsors': sponsors,
        'features': features,
    })


def logout_view(request):
    """Sign out the current member safely."""
    logout(request)
    messages.info(request, "You have been safely signed out. Thank you for visiting.")
    return redirect('home')
