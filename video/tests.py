from django.test import TestCase
from user.models import User, EmailVerify, BankCard
from django.core.files.uploadedfile import SimpleUploadedFile
import bcrypt
import datetime

default_content_type = "application/json"


class VideoTests(TestCase):
    def setUp(self) -> None:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        EmailVerify.objects.create(
            email="1234@asd.com",
            email_valid="testValid",
            email_valid_expire=datetime.date(2077, 12, 25)
        )
        EmailVerify.objects.create(
            email="new@mail.com",
            email_valid="testValid",
            email_valid_expire=datetime.date(2077, 12, 25)
        )
        bankcard = BankCard.objects.create(
            card_id="123456789",
            card_balance=100,
        )
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

    def test_upload_not_logged_in(self):
        video_content = b'\xff\x00\x00' * 100 * 100
        file = SimpleUploadedFile("video1.mp4", video_content, content_type="video/mp4")
        content = {
            "video": file
        }
        res = self.client.post("/video/", content)
        self.assertEqual(res.status_code, 401)
        self.assertJSONEqual(
            res.content, {"code": 1001, "message": "not_logged_in", "data": {}}
        )

    def test_upload(self):
        res = self.post_login("testDemand", "testPassword")
        self.assertEqual(res.status_code, 200)
        video_content = b'\xff\x00\x00' * 100 * 100
        file = SimpleUploadedFile("video1.mp4", video_content, content_type="video/mp4")
        content = {
            "video": file
        }
        res = self.client.post("/video/", content)
        self.assertEqual(res.status_code, 200)

    def test_video_handler_get_not_found(self):
        res = self.post_login("testDemand", "testPassword")
        self.assertEqual(res.status_code, 200)
        url = "111"
        res = self.client.get(f"/video/{url}")
        self.assertJSONEqual(
            res.content, {"code": 18, "message": "video not found", "data": {}}
        )

    def test_video_handler_delete_not_found(self):
        res = self.post_login("testDemand", "testPassword")
        self.assertEqual(res.status_code, 200)
        url = "111"
        res = self.client.get(f"/video/{url}")
        self.assertJSONEqual(
            res.content, {"code": 18, "message": "video not found", "data": {}}
        )

    def test_video_handler_get(self):
        res = self.post_login("testDemand", "testPassword")
        self.assertEqual(res.status_code, 200)
        video_content = b'\xff\x00\x00' * 100 * 100
        file = SimpleUploadedFile("video1.mp4", video_content, content_type="video/mp4")
        content = {
            "video": file
        }
        res = self.client.post("/video/", content)
        url = res.json()["data"]["url"]
        res = self.client.get(f"/video/{url}")
        self.assertEqual(res.status_code, 200)

    def test_video_handler_delete(self):
        res = self.post_login("testDemand", "testPassword")
        self.assertEqual(res.status_code, 200)
        video_content = b'\xff\x00\x00' * 100 * 100
        file = SimpleUploadedFile("video1.mp4", video_content, content_type="video/mp4")
        content = {
            "video": file
        }
        res = self.client.post("/video/", content)
        url = res.json()["data"]["url"]
        res = self.client.delete(f"/video/{url}")
        self.assertEqual(res.status_code, 200)
