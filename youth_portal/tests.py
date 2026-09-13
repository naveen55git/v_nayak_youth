from django.test import TestCase, Client
from django.urls import reverse
from youth_portal.models import User, MobileOTP, Sponsorship, Complaint, Festival, CommunityFeature
from youth_portal.services import generate_and_send_otp, verify_mobile_otp


class YouthPortalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_user = User.objects.create_user(
            username="testmember",
            password="password123",
            email="testmember@gmail.com",
            phone_number="9876543210",
            surname="Kumar",
            last_name="Reddy"
        )

    def test_home_page_status(self):
        """Home page loads successfully."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "V.NAYAK YOUTH")
        self.assertContains(response, "ASSOCIATION")

    def test_user_registration_success(self):
        """Registering a new member creates user in SQLite and redirects to OTP verification."""
        reg_data = {
            'surname': 'Rao',
            'last_name': 'Boda',
            'username': 'bodarao',
            'email': 'bodarao@gmail.com',
            'phone_number': '9123456780',
            'password': 'safePassword123',
            'confirm_password': 'safePassword123'
        }
        response = self.client.post(reverse('register'), reg_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('verify_otp'))

        # Check DB
        created_user = User.objects.filter(username='bodarao').first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.phone_number, '9123456780')
        self.assertEqual(created_user.surname, 'Rao')

        # Check OTP generated
        otp = MobileOTP.objects.filter(phone_number='9123456780').first()
        self.assertIsNotNone(otp)
        self.assertEqual(len(otp.otp_code), 6)

    def test_mobile_otp_generation_and_login(self):
        """Requesting OTP generates a 6-digit code, and verifying logs user in."""
        req_response = self.client.post(reverse('login_otp'), {'phone_number': '9876543210'})
        self.assertEqual(req_response.status_code, 302)
        self.assertEqual(req_response.url, reverse('verify_otp'))

        otp_record = MobileOTP.objects.filter(phone_number='9876543210', is_used=False).first()
        self.assertIsNotNone(otp_record)
        otp_code = otp_record.otp_code
        self.assertEqual(len(otp_code), 6)

        fail_response = self.client.post(reverse('verify_otp'), {'otp_code': '000000'})
        self.assertEqual(fail_response.status_code, 200)
        self.assertContains(fail_response, "Invalid OTP code")

        verify_response = self.client.post(reverse('verify_otp'), {'otp_code': otp_code})
        self.assertEqual(verify_response.status_code, 302)
        self.assertEqual(verify_response.url, reverse('dashboard'))

        dash_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dash_response.status_code, 200)
        self.assertContains(dash_response, "Welcome, Kumar Reddy")

    def test_membership_card_generation(self):
        """Authenticated member can generate and view their PVC card with 6-year tenure."""
        self.client.force_login(self.test_user)
        response = self.client.get(reverse('membership_card'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "V.NAYAK YOUTH")
        self.assertContains(response, "v Nayak youth")

        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.is_membership_active)
        self.assertTrue(self.test_user.membership_id.startswith("VNYA-") or self.test_user.membership_id.startswith("VNYM-"))

    def test_sponsor_submission_and_display(self):
        """Users can submit a sponsorship contribution."""
        response = self.client.post(reverse('sponsor'), {
            'name': 'Kavitha Nayak',
            'phone': '9876500000',
            'amount': '1500',
            'message': 'For Sports Ground'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('sponsor'))

        sp = Sponsorship.objects.filter(name='Kavitha Nayak').first()
        self.assertIsNotNone(sp)
        self.assertEqual(float(sp.amount), 1500.0)

    def test_complaint_submission(self):
        """Users can lodge a grievance."""
        response = self.client.post(reverse('complaints'), {
            'name_or_id': 'V. Ramesh',
            'phone': '9876511111',
            'subject': 'Sports ground net replacement',
            'description': 'Volleyball net needs urgent replacement for upcoming tournament.'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('complaints'))

        cp = Complaint.objects.filter(phone='9876511111').first()
        self.assertIsNotNone(cp)
        self.assertEqual(cp.status, 'PENDING')

    def test_logout(self):
        """Logging out ends the authenticated session."""
        self.client.force_login(self.test_user)
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))

        dash_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dash_response.status_code, 302)
