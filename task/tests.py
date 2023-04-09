# Create your tests here.
from django.test import TestCase
from user.models import User
from task.models import Question, Current_tag_user, Task
import bcrypt
import datetime

default_content_type = "application/json"


class TaskTests(TestCase):
    def setUp(self) -> None:
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
            publisher=test_publisher,
            task_id=1,
            distribute_user_num=0,
            task_name="testTask"
        )
        question1 = Question.objects.create(
            q_id=0,
            data="string",
            task=task,
            data_type="text",
        )
        #
        # test_data = TextData.objects.create(
        #     data=[
        #         {
        #             "q_id": 0,
        #             "data": "string"
        #         },
        #         {
        #             "q_id": 1,
        #             "data": "string"
        #         },
        #     ]
        # )
        #
        # test_result = Result.objects.create(
        #     tag_user=test_receiver1,
        #     tag_res="string",
        # )

        current_tag_user = Current_tag_user.objects.create(
            tag_user=test_receiver1,
            accepted_at=datetime.datetime.now().timestamp(),
        )
        task.current_tag_user_list.add(current_tag_user)
        task.past_tag_user_list.add(test_receiver2)
        task.questions.add(question1)
        task.publisher = test_publisher
        task.save()

    def post_task(self, para: dict):
        return self.client.post("/task/", para, content_type=default_content_type)

    def test_create_task_not_logged_in(self):
        para = {
            "task_type": "image",
            "task_style": "string",
            "reward_per_q": 0,
            "time_limit_per_q": 0,
            "total_time_limit": 0,
            "distribute_user_num": 1,
            "task_name": "testTask",
            "accept_method": "auto",
        }
        res = self.post_task(para)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["message"], "not_logged_in")

    def test_create_task_success(self):
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        para = {
            "task_type": "image",
            "task_style": "string",
            "reward_per_q": 0,
            "time_limit_per_q": 0,
            "total_time_limit": 0,
            "distribute_user_num": 1,
            "task_name": "testTask",
            "accept_method": "auto",
            "files": [1, 2, 3, 4]
        }
        res = self.post_task(para)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")

    def test_create_task_score_not_enough(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        para = {
            "task_type": "image",
            "task_style": "string",
            "reward_per_q": 100,
            "time_limit_per_q": 0,
            "total_time_limit": 0,
            "distribute_user_num": 10,
            "task_name": "testTask",
            "accept_method": "auto",
            "files": [1, 2, 3, 4]
        }
        res = self.post_task(para)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 10)

    def test_modify_task_not_logged_in(self):
        res = self.client.put("/task/1", {}, content_type=default_content_type)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["message"], "not_logged_in")

    def test_modify_task_not_existed(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.put("/task/10000000003924924", {}, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 11)

    def test_modify_task_success(self):
        # 首先创建一个
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        para = {
            "task_type": "image",
            "task_style": "string",
            "reward_per_q": 0,
            "time_limit_per_q": 0,
            "total_time_limit": 0,
            "distribute_user_num": 1,
            "task_name": "testTask",
            "accept_method": "auto",
            "files": [1, 2, 3, 4]
        }
        res = self.post_task(para)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")

        para2 = {
            "task_type": "image",
            "task_style": "string",
            "reward_per_q": 2,
            "time_limit_per_q": 3,
            "total_time_limit": 4,
            "distribute_user_num": 5,
            "task_name": "NewTestTask",
            "accept_method": "auto",
            "files": [1, 2, 3, 4]
        }
        res2 = self.client.put('/task/1', para2, content_type=default_content_type)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["data"], {"task_id": 1})

    def test_delete_task_not_logged_in(self):
        res = self.client.delete("/task/1")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["message"], "not_logged_in")

    def test_delete_task_not_existed(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.delete("/task/10000000003924924")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 11)

    def test_delete_task_success(self):
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        para = {
            "task_type": "image",
            "task_style": "string",
            "reward_per_q": 0,
            "time_limit_per_q": 0,
            "total_time_limit": 0,
            "distribute_user_num": 1,
            "task_name": "testTask",
            "accept_method": "auto",
            "files": [1, 2, 3, 4]
        }
        res = self.post_task(para)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")

        res = self.client.delete("/task/1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Task.objects.filter(task_id=1).count(), 0)

    def test_get_task_not_logged_in(self):
        res = self.client.get("/task/1")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["message"], "not_logged_in")

    def test_get_task_not_existed(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get("/task/10000000003924924")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 11)

    def test_get_task_success(self):
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        para = {
            "task_type": "image",
            "task_style": "string",
            "reward_per_q": 0,
            "time_limit_per_q": 0,
            "total_time_limit": 0,
            "distribute_user_num": 1,
            "task_name": "testTask",
            "accept_method": "auto",
            "files": [1, 2, 3, 4]
        }
        res = self.post_task(para)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")

        res = self.client.get("/task/1")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"], Task.objects.get(task_id=1).serialize())

    def test_get_all_tasks(self):
        res = self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        res = self.client.get("/task/get_all_tasks")
        tasks = Task.objects.all()
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(res.content, {
            "code": 0,
            "message": "Succeed",
            "data": [task.serialize() for task in tasks]
        })

    def test_get_my_tasks_publisher(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        res2 = self.client.get("/task/get_my_tasks")
        task = Task.objects.filter(publisher=User.objects.get(user_name="testPublisher"))
        self.assertJSONEqual(res2.content, {
            "code": 0,
            "message": "Succeed",
            "data": [task.serialize() for task in task]
        })
        self.assertEqual(res2.status_code, 200)

    def test_upload_data(self):
        # 以需求方的身份登录
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        # open file
        with open("task/data/upload_test_1.zip", "rb") as fp:
            data = {
                "file": fp
            }
            res2 = self.client.post("/task/upload_data?data_type=text", data)
            self.assertEqual(res2.json()["data"]["legal_num"], 0)
            # self.assertEqual(res2.json()["message"], "Succeed")
            # self.assertEqual(res2.status_code, 200)

    # def test_res_data(self):
    #     # 以需求方的身份登录
    #     res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
    #                            content_type=default_content_type)
    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(res.json()["message"], "Succeed")
    #     result_offered = {
    #         "result": [
    #             {
    #                 "q_id": 0,
    #                 "res": "string"
    #             }
    #         ]
    #     }
    #     res2 = self.client.post(f"/task/upload_res/{1}", result_offered, content_type=default_content_type)
    #     self.assertEqual(res2.status_code, 200)
    #     self.assertEqual(res2.json()["message"], "Succeed")

    # def test_upload_res_not_login(self):
    #     res = self.client.post(f"/task/upload_res/{1}")
    #     self.assertJSONEqual(res.content, {"code": 1001, "message": "not_logged_in", "data": {}, })
