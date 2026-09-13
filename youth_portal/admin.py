from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, MobileOTP, CommunityFeature, GalleryImage, Festival, Sponsorship, Complaint


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'surname', 'last_name', 'phone_number', 'email', 'membership_id', 'is_membership_active', 'is_staff')
    list_filter = ('is_membership_active', 'is_staff', 'is_superuser', 'caste')
    search_fields = ('username', 'surname', 'last_name', 'phone_number', 'email', 'membership_id', 'aadhaar_number')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Youth Member Info', {
            'fields': ('surname', 'phone_number', 'caste', 'aadhaar_number', 'address', 'tenure', 'photo', 'avatar', 'membership_id', 'is_membership_active')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Youth Member Info', {
            'fields': ('surname', 'phone_number', 'email')
        }),
    )


@admin.register(MobileOTP)
class MobileOTPAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'otp_code', 'created_at', 'expires_at', 'is_used', 'is_valid_display')
    list_filter = ('is_used', 'created_at')
    search_fields = ('phone_number', 'otp_code')

    def is_valid_display(self, obj):
        return obj.is_valid()
    is_valid_display.boolean = True
    is_valid_display.short_description = "Active / Valid"


@admin.register(CommunityFeature)
class CommunityFeatureAdmin(admin.ModelAdmin):
    list_display = ('title', 'badge', 'link', 'created_at')
    search_fields = ('title', 'description', 'badge')


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)


@admin.register(Festival)
class FestivalAdmin(admin.ModelAdmin):
    list_display = ('name', 'date_text', 'created_at')
    search_fields = ('name', 'description')


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'amount', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('name', 'phone', 'message')


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'name_or_id', 'phone', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('subject', 'name_or_id', 'phone', 'description')
