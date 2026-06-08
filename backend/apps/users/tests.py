from django.urls import reverse
from rest_framework.test import APITestCase

from .models import User


class RegisterPhoneValidationTests(APITestCase):
    def test_register_rejects_invalid_phone(self):
        response = self.client.post(
            reverse('api_register'),
            {
                'full_name': 'Test User',
                'email': 'invalid-phone@example.com',
                'phone': '43194819348',
                'password': 'Password123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('phone', response.data)

    def test_register_accepts_local_phone_and_normalizes(self):
        response = self.client.post(
            reverse('api_register'),
            {
                'full_name': 'Valid User',
                'email': 'valid-phone@example.com',
                'phone': '09 123 456 78',
                'password': 'Password123',
            },
            format='json',
        )

        print(response.data)  # debug
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email='valid-phone@example.com')
        self.assertEqual(user.phone, '0912345678')