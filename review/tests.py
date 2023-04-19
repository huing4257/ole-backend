from django.test import TestCase
import bcrypt
from user.models import User
from task.models import Task
import datetime

default_content_type = "application/json"


# Create your tests here.
class ReviewTests(TestCase):
    para = {
        "task_type": "image",
        "task_style": "string",
        "reward_per_q": 0,
        "time_limit_per_q": 0,
        "total_time_limit": 0,
        "distribute_user_num": 1,
        "task_name": "testTask",
        "accept_method": "auto",
        "files": [1],
        "tag_type": ["tag1", "tag2", "tag3"],
        "stdans_tag": ""
    }

    def setUp(self) -> None:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        test_publisher = User.objects.create(
            user_id=1,
            user_name="testPublisher",
            password=hashed_password,
            user_type="demand",
            score=100,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
        )
        test_publisher.save()
        test_receiver1 = User.objects.create(
            user_id=2,
            user_name="testReceiver1",
            password=hashed_password,
            user_type="tag",
            credit_score=100,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
        )
        test_receiver1.save()

    def login(self, username):
        response = self.client.post("/user/login", {
            "user_name": username,
            "password": "testPassword"
        }, content_type=default_content_type)
        return response

    def test_manual_check_success(self):
        res = self.login("testPublisher")
        self.assertEqual(res.status_code, 200)
        res = self.client.post("/task/", self.para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()["data"]["task_id"]
        res = self.client.post(f"/task/distribute/{task_id}")
        self.assertEqual(res.status_code, 200)

        self.client.post("/user/logout")
        res = self.login("testReceiver1")
        self.assertEqual(res.status_code, 200)
        res = self.client.post(f"/task/accept/{task_id}")
        js = res.json()
        self.assertEqual(res.status_code, 200)
        res = self.client.post(f"/task/upload_res/{task_id}/1", {
            "result": "tag_1"
        }, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)

        self.client.post("/user/logout")
        res = self.login("testPublisher")
        self.assertEqual(res.status_code, 200)

        res = self.client.post(f"/review/manual_check/{task_id}/2", {
            "check_method": "select"}, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"]["q_info"][0]["result"]["tag_res"], "tag_1")

