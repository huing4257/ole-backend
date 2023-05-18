from django.test import TestCase
from user.models import User, BankCard
import bcrypt
import datetime
default_content_type = "application/json"


class AdvertiseTests(TestCase):
    def setUp(self):
        bankcard = BankCard.objects.create(
            card_id="123456789",
            card_balance=100,
        )
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        User.objects.create(
            user_id=1,
            user_name="testUser",
            password=hashed_password,  # store hashed password as a string
            user_type="admin",
            score=1000,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
            bank_account=bankcard,
        )
        User.objects.create(
            user_id=2,
            user_name="testTag",
            password=hashed_password,  # store hashed password as a string
            user_type="tag",
            score=1000,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
        )
        User.objects.create(
            user_id=3,
            user_name="testDemand",
            password=hashed_password,  # store hashed password as a string
            user_type="demand",
            score=1000,
            membership_level=0,
            invite_code="testInviteCode",
        )
        User.objects.create(
            user_id=4,
            user_name="testAgent",
            password=hashed_password,
            user_type="agent",
            score=0,
            membership_level=0,
            invite_code="testInviteCode",
        )
        
    def post_login(self, user_name, password):
        payload = {
            "user_name": user_name,
            "password": password,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.client.post("/user/login", payload, content_type=default_content_type)        