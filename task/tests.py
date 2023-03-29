# Create your tests here.
from django.test import TestCase
from user.models import User
from task.models import Task, Result, Data
import bcrypt
import datetime

default_content_type = "application/json"


class TaskTests(TestCase):
    def setUp(self) -> None:
        test_data = Data.objects.create(
            data=[
                {
                    "q_id": 0,
                    "data": "string"
                },
                {
                    "q_id": 1,
                    "data": "string"
                },
            ]
        )

        test_result = Result.objects.create(
            user_id=3,
            result=[
                {
                    "user_id": 2,
                    "data": {}
                },
                {
                    "user_id": 3,
                    "data": {}
                },
            ]
        )
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        test_publisher = User.objects.create(
            user_id=1,
            user_name="testPublisher",
            password=hashed_password,  # store hashed password as a string
            user_type="demand",
            score=100,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
        )
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        test_receiver1 = User.objects.create(
            user_id=2,
            user_name="testReceiver1",
            password=hashed_password,  # store hashed password as a string
            user_type="tag",
            score=0,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
        )
        test_receiver2 = User.objects.create(
            user_id=3,
            user_name="testReceiver2",
            password=hashed_password,  # store hashed password as a string
            user_type="tag",
            score=0,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
        )

        task = Task.objects.create(
            task_type="",
            task_style="",
            reward_per_q=0,
            time_limit_per_q=1,
            total_time_limit=1,
            auto_ac=False,
            manual_ac=True,
            publisher=test_publisher,
            task_id=1,
            distribute_user_num=0,
            task_name="testTask"
        )

        task.data.add(test_data)
        task.distribute_users.add(test_receiver1)
        task.distribute_user_num += 1
        task.distribute_users.add(test_receiver2)
        task.distribute_user_num += 1
        task.result.add(test_result)

    def post_task(self, para: dict):
        return self.client.post("/task", para, content_type=default_content_type)

    def test_create_task_success(self):
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        para = {
            "task_type": "picture",
            "task_style": "string",
            "reward_per_q": 10,
            "time_limit_per_q": 0,
            "total_time_limit": 0,
            "auto_ac": True,
            "manual_ac": True,
            "distribute_user_num": 1,
        }
        res = self.post_task(para)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")

    def test_create_task_not_logged_in(self):
        para = {
            "task_type": "picture",
            "task_style": "string",
            "reward_per_q": 0,
            "time_limit_per_q": 0,
            "total_time_limit": 0,
            "auto_ac": True,
            "manual_ac": True,
            "distribute_user_num": 1
        }
        res = self.post_task(para)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["message"], "not_logged_in")

    def test_create_task_score_not_enough(self):
        pass

    # def test_get_my_tasks(self):
    #     # 以需求方的身份登录
    #     res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
    #                            content_type=default_content_type)
    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(res.json()["message"], "Succeed")
    #     res2 = self.client.get("/task/get_my_tasks")
    #     task: Task = Task.objects.filter(task_id=1).first()
    #     self.assertJSONEqual(res2.content, {
    #         "code": 0,
    #         "message": "Succeed",
    #         "data": [task.serialize()]
    #     })
    #     self.assertEqual(res2.status_code, 200)

    def test_upload_data(self):
        # 以需求方的身份登录
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        data_offered = {
            "data": [
                {
                    "q_id": 0,
                    "data": "string"
                }
            ]
        }
        res2 = self.client.post(f"/task/upload_data/{1}", data_offered, content_type=default_content_type)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["message"], "Succeed")

    def test_upload_data_not_login(self):
        res = self.client.post(f"/task/upload_data/{1}")
        self.assertJSONEqual(res.content, {"code": 1001, "message": "not_logged_in", "data": {}, })        

    def test_res_data(self):
        # 以需求方的身份登录
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        result_offered = {
            "result": [
                {
                    "q_id": 0,
                    "res": "string"
                }
            ]
        }
        res2 = self.client.post(f"/task/upload_res/{1}", result_offered, content_type=default_content_type)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["message"], "Succeed")        

    def test_upload_res_not_login(self):
        res = self.client.post(f"/task/upload_res/{1}")
        self.assertJSONEqual(res.content, {"code": 1001, "message": "not_logged_in", "data": {}, })          