from django.core.management.base import BaseCommand
from youth_portal.models import User, CommunityFeature, Festival, Sponsorship


class Command(BaseCommand):
    help = "Seed initial admin, test youth members, festivals, features, and sponsors"

    def handle(self, *args, **options):
        # 1. Seed standard member 'nayak'
        if not User.objects.filter(username="nayak").exists():
            user = User.objects.create_superuser(
                username="nayak",
                email="mrwhitedevil2003@gmail.com",
                password="password123",
                surname="Vangala",
                last_name="Nayak",
                phone_number="9347624977",
                caste="ST (Lambada)",
                aadhaar_number="XXXX XXXX 1234",
                address="st-colony ,madharam village ,singareni MLD,khammam district Telangana 507122",
                membership_id="VNYA-2026-1001",
                tenure="2026 - 2032 (6 Years Official Term)",
                is_membership_active=True
            )
            self.stdout.write(self.style.SUCCESS(f"Created seed user: {user.username} (Mobile: {user.phone_number})"))
        else:
            self.stdout.write(self.style.WARNING("Seed user 'nayak' already exists."))

        # 2. Seed Admin user 'Admin@2026' from file2.html
        if not User.objects.filter(username="Admin@2026").exists():
            admin_user = User.objects.create_superuser(
                username="Admin@2026",
                email="admin@vnayakyouth.org",
                password="Admin@2026",
                surname="Secretariat",
                last_name="Admin",
                phone_number="9100894417",
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS(f"Created Secretariat Admin user: {admin_user.username}"))

        # 3. Seed Community Features
        if not CommunityFeature.objects.exists():
            CommunityFeature.objects.create(
                title="Madharam Premier Youth Cricket Trophy",
                badge="SPORTS 2026",
                description="Annual cricket tournament registration open for all local teams in Singareni Mandal. Official Association ID card is mandatory.",
                link=""
            )
            CommunityFeature.objects.create(
                title="Sant Sevalal Maharaj Jayanti Preparations",
                badge="FESTIVAL",
                description="Grand religious celebrations and youth volunteer committees are being formed for ST-Colony grand procession.",
                link=""
            )
            CommunityFeature.objects.create(
                title="24/7 Khammam Emergency Blood Donors Network",
                badge="EMERGENCY",
                description="Instant emergency blood donors coordination across Khammam and Kothagudem hospital centers. Contact 9347624977.",
                link="tel:9347624977"
            )
            self.stdout.write(self.style.SUCCESS("Created default community announcements."))

        # 4. Seed Festivals
        if not Festival.objects.exists():
            Festival.objects.create(
                name="Sant Sevalal Maharaj Jayanti",
                date_text="15 February 2026",
                description="Grand religious procession, community prayers (Bhog Bhandara), cultural Lambada folk dance performances, and youth seva in ST-Colony."
            )
            Festival.objects.create(
                name="Teej Festival Celebrations",
                date_text="August (Monsoon Season)",
                description="Traditional 9-day wheat seedling festival celebrated by village youth with traditional dances, singing, and cultural unity."
            )
            self.stdout.write(self.style.SUCCESS("Created default festival celebrations."))

        # 5. Seed Sponsors
        if not Sponsorship.objects.exists():
            Sponsorship.objects.create(
                name="Mood bhanu Prasad",
                phone="9100894417",
                amount=5000,
                message="Youth Tournament Ground Equipment",
                is_verified=True
            )
            Sponsorship.objects.create(
                name="Ramesh Nayak",
                phone="9347624977",
                amount=2500,
                message="Festival Food Annadanam",
                is_verified=True
            )
            self.stdout.write(self.style.SUCCESS("Created default verified sponsors."))
