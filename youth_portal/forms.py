from django import forms
from django.core.exceptions import ValidationError
from .models import User, Sponsorship, Complaint, CommunityFeature, GalleryImage, Festival
from .services import clean_phone_number


class YouthRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'At least 6 characters',
            'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 transition',
            'minlength': '6'
        }),
        label="Password *"
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Repeat password',
            'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 transition',
            'minlength': '6'
        }),
        label="Confirm Password *"
    )

    class Meta:
        model = User
        fields = ['surname', 'last_name', 'username', 'email', 'phone_number', 'password']
        widgets = {
            'surname': forms.TextInput(attrs={
                'placeholder': 'e.g., Vangala',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 transition'
            }),
            'last_name': forms.TextInput(attrs={
                'placeholder': 'e.g., Nayak',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 transition'
            }),
            'username': forms.TextInput(attrs={
                'placeholder': 'e.g., vnayak_youth',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl pl-8 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 font-mono transition'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'yourname@gmail.com',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 font-mono transition'
            }),
            'phone_number': forms.TextInput(attrs={
                'placeholder': '10-digit mobile number',
                'maxlength': '10',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 font-mono transition'
            }),
        }

    def clean_phone_number(self):
        phone = clean_phone_number(self.cleaned_data.get('phone_number', ''))
        if len(phone) != 10:
            raise ValidationError("Please enter a valid 10-digit mobile number.")
        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError("This mobile number is already registered. Please log in.")
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email address is already registered.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip().lower()
        if User.objects.filter(username=username).exists():
            raise ValidationError("This User ID is already taken. Please choose another.")
        return username

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Password and Confirm Password do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class EmailRequestOTPForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter registered Gmail / Email address',
            'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-3 text-sm text-white focus:outline-none focus:border-amber-500 font-mono transition',
            'autofocus': 'autofocus'
        }),
        label="Registered Email Address *"
    )

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not User.objects.filter(email=email).exists():
            raise ValidationError("No registered account found with this email address. Please register first.")
        return email


# Compatibility alias
MobileRequestOTPForm = EmailRequestOTPForm



class VerifyOTPForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter 6-digit OTP',
            'maxlength': '6',
            'class': 'w-full bg-slate-950 border-2 border-amber-500/50 rounded-xl px-4 py-3 text-center text-2xl tracking-[0.5em] text-amber-300 focus:outline-none focus:border-amber-400 font-mono font-black transition',
            'autocomplete': 'one-time-code',
            'autofocus': 'autofocus'
        }),
        label="6-Digit OTP Code *"
    )

    def clean_otp_code(self):
        code = self.cleaned_data.get('otp_code', '').strip()
        if not code.isdigit() or len(code) != 6:
            raise ValidationError("OTP must be exactly 6 numeric digits.")
        return code


class MembershipDetailsForm(forms.ModelForm):
    TENURE_CHOICES = [
        ("2026 - 2032 (6 Years Official Term)", "2026 - 2032 (Standard 6-Year Youth Association Tenure)"),
        ("2026 - 2033 (7 Years Permanent Term)", "2026 - 2033 (7-Year Senior Youth Tenure)"),
        ("2026 - 2036 (10 Years Lifetime Founding Member)", "2026 - 2036 (10-Year Founder Tenure)"),
    ]

    tenure = forms.ChoiceField(
        choices=TENURE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-amber-500 transition'
        }),
        label="Membership Tenure (Minimum 6-Year Term) *"
    )

    class Meta:
        model = User
        fields = ['surname', 'last_name', 'caste', 'aadhaar_number', 'phone_number', 'email', 'tenure', 'address', 'photo']
        widgets = {
            'surname': forms.TextInput(attrs={
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-amber-500 transition'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-amber-500 transition'
            }),
            'caste': forms.TextInput(attrs={
                'placeholder': 'e.g., ST (Lambada) / BC / General',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-amber-500 transition'
            }),
            'aadhaar_number': forms.TextInput(attrs={
                'placeholder': 'XXXX XXXX XXXX (12 Digits)',
                'maxlength': '14',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-amber-500 font-mono transition'
            }),
            'phone_number': forms.TextInput(attrs={
                'maxlength': '10',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-amber-500 font-mono transition'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-amber-500 font-mono transition'
            }),
            'address': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'H.No, Street, ST-Colony, Madharam Village, Singareni Mandal, Khammam District',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-amber-500 transition'
            }),
            'photo': forms.FileInput(attrs={
                'accept': 'image/jpeg,image/png,image/webp',
                'class': 'hidden',
                'id': 'photoInput'
            }),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and hasattr(photo, 'size'):
            size_kb = photo.size / 1024
            # Between 10 KB and 2 MB
            if size_kb < 10.0 or size_kb > 2048.0:
                raise ValidationError(
                    f"Photo file size ({size_kb:.1f} KB) is invalid! It must strictly be between 10 KB and 2 MB."
                )
        return photo

    def clean_aadhaar_number(self):
        aadhaar = self.cleaned_data.get('aadhaar_number', '')
        digits = ''.join(c for c in aadhaar if c.isdigit())
        if digits and len(digits) != 12:
            raise ValidationError("Aadhaar Number must have exactly 12 digits.")
        if len(digits) == 12:
            return f"XXXX XXXX {digits[-4:]}"
        return aadhaar


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['surname', 'last_name', 'email', 'phone_number', 'avatar']
        widgets = {
            'surname': forms.TextInput(attrs={
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 font-mono'
            }),
            'phone_number': forms.TextInput(attrs={
                'maxlength': '10',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 font-mono'
            }),
            'avatar': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'text-xs text-slate-400 file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-bold file:bg-slate-800 file:text-amber-300 hover:file:bg-slate-700'
            })
        }


class SponsorshipForm(forms.ModelForm):
    class Meta:
        model = Sponsorship
        fields = ['name', 'phone', 'amount', 'screenshot', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g. Ramesh Rathod',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 transition'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '10-digit number',
                'maxlength': '10',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 font-mono transition'
            }),
            'amount': forms.NumberInput(attrs={
                'placeholder': 'Amount in INR (₹)',
                'min': '1',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 font-mono transition'
            }),
            'screenshot': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-slate-800 file:text-amber-300 hover:file:bg-slate-700 bg-slate-950 p-2 rounded-xl border border-slate-800'
            }),
            'message': forms.TextInput(attrs={
                'placeholder': 'e.g. For Cricket tournament / Jayanti celebration',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 transition'
            }),
        }


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['name_or_id', 'phone', 'subject', 'description', 'image']
        widgets = {
            'name_or_id': forms.TextInput(attrs={
                'placeholder': 'Enter your name or User ID',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 transition'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '10-digit phone',
                'maxlength': '10',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 font-mono transition'
            }),
            'subject': forms.TextInput(attrs={
                'placeholder': 'e.g. Ground maintenance / Drinking water near community hall',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 transition'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe the grievance clearly...',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-amber-500 transition'
            }),
            'image': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-slate-800 file:text-amber-300 hover:file:bg-slate-700 bg-slate-950 p-2 rounded-xl border border-slate-800'
            }),
        }


class CommunityFeatureForm(forms.ModelForm):
    class Meta:
        model = CommunityFeature
        fields = ['title', 'badge', 'description', 'link']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g. Cricket Tournament 2026 Schedule',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500'
            }),
            'badge': forms.TextInput(attrs={
                'placeholder': 'e.g. NEW / SPORTS / URGENT',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 uppercase font-mono'
            }),
            'link': forms.URLInput(attrs={
                'placeholder': 'https://... (Optional)',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500 font-mono'
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Describe what is coming or the instructions for members...',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-amber-500'
            }),
        }


class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ['title', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g. Village Youth Cricket Match',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-amber-500'
            }),
            'image': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'w-full text-xs text-slate-400 bg-slate-950 p-2 rounded-xl border border-slate-800'
            })
        }


class FestivalForm(forms.ModelForm):
    class Meta:
        model = Festival
        fields = ['name', 'date_text', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g. Sant Sevalal Maharaj Jayanti',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white focus:outline-none focus:border-amber-500'
            }),
            'date_text': forms.TextInput(attrs={
                'placeholder': 'e.g. 15 February 2026',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white focus:outline-none focus:border-amber-500'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe youth programs, prayers, and arrangements...',
                'class': 'w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white focus:outline-none focus:border-amber-500'
            }),
            'image': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'w-full text-xs text-slate-400 bg-slate-950 p-2 rounded-xl border border-slate-800'
            })
        }
