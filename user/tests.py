import random
from django.test import TestCase, Client
from user.models import User
import bcrypt


class UserTests(TestCase):
    def setUp(self):
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        User.objects.create(
            user_id=0,
            user_name="testUser",
            password=hashed_password.decode("utf-8"),  # store hashed password as a string
            user_type="admin",
            score=0,
            membership_level=0,
            invite_code="testInviteCode",
        )

    def post_user(self, user_name, password):
        payload = {
            "user_name": user_name,
            "password": password,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.client.post("/user/login", payload, content_type="application/json")

    def test_login(self):
        user_name = "testUser"
        password = "testPassword"
        self.post_user(user_name, password)
        payload = {
            "user_name": user_name,
            "password": password,
        }
        response = self.client.post("/user/login", payload)
        self.assertEqual(response.status_code, 200)
