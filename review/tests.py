from django.test import TestCase
import bcrypt
from user.models import User
from review.models import AnsList
from django.core.files.uploadedfile import SimpleUploadedFile
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

    def login_create_task(self, distribute_user_num=1):
        res = self.login("testPublisher")
        self.assertEqual(res.status_code, 200)
        para = self.para.copy()
        para["distribute_user_num"] = distribute_user_num
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()["data"]["task_id"]
        return task_id

    def test_manual_check_success(self):
        task_id = self.login_create_task()
        res = self.client.post(f"/task/distribute/{task_id}")
        self.assertEqual(res.status_code, 200)

        self.client.post("/user/logout")
        res = self.login("testReceiver1")
        self.assertEqual(res.status_code, 200)
        res = self.client.post(f"/task/accept/{task_id}")
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

    def test_manual_check_no_permission(self):
        self.login("testPublisher")
        res = self.client.post("/task/", self.para, content_type=default_content_type)
        task_id = res.json()["data"]["task_id"]

        self.client.post("/user/logout")
        self.login("testReceiver1")

        res = self.client.post(f"/review/manual_check/{task_id}/2", {"check_method": "select"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 16)

    def test_upload_stdans_success(self):
        self.login_create_task()
        with open("a.csv", "w") as f:
            f.write("1.txt,tag_1_1")
        file = SimpleUploadedFile("a.csv", open("a.csv", "rb").read())
        res = self.client.post("/review/upload_stdans", {
            "file": file
        })
        ans_id = res.json()["data"]
        self.assertEqual(res.status_code, 200)
        self.assertTrue(AnsList.objects.filter(id=int(ans_id)).exists())

    def test_review_accept(self):
        task_id = self.login_create_task()
        self.client.post(f"/task/distribute/{task_id}")
        res = self.client.post(f"/review/accept/{task_id}/2")
        self.assertEqual(res.status_code, 200)

    def test_review_acc_not_distributed(self):
        task_id = self.login_create_task()
        res = self.client.post(f"/review/accept/{task_id}/2")
        self.assertEqual(res.status_code, 400)

    def test_review_reject(self):
        task_id = self.login_create_task()
        self.client.post(f"/task/distribute/{task_id}")
        res = self.client.post(f"/review/refuse/{task_id}/2")
        self.assertEqual(res.status_code, 200)

    def test_download_task_not_finish(self):
        task_id = self.login_create_task()
        self.client.post(f"/task/distribute/{task_id}")
        # receiver id = 2
        res = self.client.get(f"/review/download/{task_id}")
        self.assertJSONEqual(res.content, {"code": 25, "message": "review not finish", "data": {}})
        self.assertEqual(res.status_code, 400)

    # def test_download_task_success(self):
    #     task_id = self.login_create_task()
    #     user_id = 2
    #     self.client.post(f"/task/distribute/{task_id}")
    #     self.client.post(f"/review/accept/{task_id}/{user_id}")
    #     # receiver id = 2
    #     res = self.client.get(f"/review/download/{task_id}")
    #     print(res.content)
    #     self.assertEqual(res.status_code, 400)

    # def test_download_task_user(self):
    #     task_id = self.login_create_task()
    #     self.client.post(f"/task/distribute/{task_id}")
    #     self.client.post(f"/review/accept/{task_id}/{user_id}")

    #     # receiver id = 2
    #     res = self.client.get(f"/review/download/{task_id}/2")        
    #     self.assertEqual(res.status_code, 200)
