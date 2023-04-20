import datetime
import bcrypt
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from picbed.models import Image
from user.models import User

# Create your tests here.

default_content_type = "application/json"


class PicbedTests(TestCase):
    def setUp(self):
        self.image_content = b'\xff\x00\x00' * 100 * 100
        image_file = SimpleUploadedFile('test_image.jpg', self.image_content, content_type='image/jpeg')
        image = Image.objects.create(
            img_file=image_file
        )
        self.img_path = image.img_file.name
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        User.objects.create(
            user_id=1,
            user_name="testPublisher",
            password=hashed_password,  # store hashed password as a string
            user_type="demand",
            score=100,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
        )

    def test_upload_image_not_logged_in(self):
        image_content = b'\xff\x00\x00' * 100 * 100
        image_file = SimpleUploadedFile('test_image.jpg', image_content, content_type='image/jpeg')
        res = self.client.post("/picbed/", {'img': image_file})
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['message'], "not_logged_in")

    def test_upload_image_success(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        image_content = b'\xff\x00\x00' * 100 * 100
        image_file = SimpleUploadedFile('test_image.jpg', image_content, content_type='image/jpeg')
        res = self.client.post("/picbed/", {'img': image_file})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['message'], "Succeed")

    def test_get_image_success(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get(f"/picbed/{self.img_path}")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, self.image_content)

    def test_get_image_pic_not_found(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get(f"/picbed/{self.img_path}/not_found")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()['code'], 18)

    def test_get_image_not_logged_in(self):
        res = self.client.get(f"/picbed/{self.img_path}")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['message'], "not_logged_in")

    def test_del_image_success(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.delete(f"/picbed/{self.img_path}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['message'], "Succeed")
        res = self.client.get(f"/picbed/{self.img_path}")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()['code'], 18)

    def test_del_image_not_logged_in(self):
        res = self.client.delete(f"/picbed/{self.img_path}")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()['message'], "not_logged_in")

    def test_del_image_pic_not_found(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.delete(f"/picbed/{self.img_path}/not_found")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()['code'], 18)
