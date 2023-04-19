# Create your tests here.
from django.test import TestCase
from user.models import User
from task.models import Question, Current_tag_user, Task, TextData, TagType
import bcrypt
import datetime

default_content_type = "application/json"


class TaskTests(TestCase):
    para = {
        "task_type": "image",
        "task_style": "string",
        "reward_per_q": 0,
        "time_limit_per_q": 0,
        "total_time_limit": 0,
        "distribute_user_num": 1,
        "task_name": "testTask",
        "accept_method": "auto",
        "files": [1, 2, 3, 4],
        "tag_type": ["tag1", "tag2", "tag3"],
        "stdans_tag": ""
    }

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
            credit_score=80,
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
            credit_score=90,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
        )

        User.objects.create(
            user_id=4,
            user_name="testReceiver3",
            password=hashed_password,  # store hashed password as a string
            user_type="tag",
            score=0,
            membership_level=0,
            credit_score=100,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
        )

        tag_list = ["tag1", "tag2", "tag3"]
        for tag in tag_list:
            TagType.objects.create(
                type_name=tag
            )
        tag_type_list = TagType.objects.all()

        task = Task.objects.create(
            task_type="text",
            task_style="",
            reward_per_q=0,
            time_limit_per_q=1,
            total_time_limit=1,
            publisher=test_publisher,
            task_id=1,
            distribute_user_num=0,
            task_name="testTask",
        )
        task.tag_type.set(tag_type_list)
        question1 = Question.objects.create(
            q_id=1,
            data="1",
            data_type="text",
        )
        question1.tag_type.set(tag_type_list)
        question2 = Question.objects.create(
            q_id=2,
            data="1",
            data_type="text",
        )
        question2.tag_type.set(tag_type_list)

        TextData.objects.create(
            data="string"
        )
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
        task.questions.add(question2)
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
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)

        res = self.post_task(self.para)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")

    def test_create_task_score_not_enough(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        para = self.para.copy()
        para["reward_per_q"] = 10000000
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
        res = self.post_task(self.para)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")

        para2 = self.para.copy()
        para2["task_name"] = "testTask2"
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
        assert res.status_code == 200
        res = self.post_task(self.para)
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
            self.assertEqual(res2.status_code, 200)

            self.assertEqual(res2.json()["message"], "Succeed")
            self.assertEqual(len(res2.json()["data"]), 3)

    def test_upload_result(self):
        # 以需求方的身份登录
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        data = {
            "result": [
                "testString",
            ]
        }
        res = self.client.post("/task/upload_res/1/1", data, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        res = self.client.post("/task/upload_res/1/2", data, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")

    # bug here
    # def test_get_task_question_publisher(self):
    #     res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
    #                            content_type=default_content_type)
    #     self.assertEqual(res.status_code, 200)
    #     res = self.client.get(f"/task/{1}/{1}")
    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(res.json()["message"], "Succeed")
    #     self.assertEqual(res.json()["data"], Question.objects.get(q_id=1).serialize(detail=True))

    # bug here
    # def test_get_task_question_receiver(self):
    #     self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
    #                      content_type=default_content_type)
    #     res = self.client.get(f"/task/{1}/{2}")
    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(res.json()["message"], "Succeed")
    #     self.assertEqual(res.json()["data"], Question.objects.get(q_id=2).serialize(detail=True))

    def test_get_task_question_not_receiver(self):
        self.client.post("/user/login", {"user_name": "testReceiver2", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get(f"/task/{1}/{1}")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["message"], "no access permission")

    # bug here
    def test_distribute_success(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        para = self.para.copy()
        para["distribute_user_num"] = 2
        res = self.post_task(para)
        self.assertEqual(res.status_code, 200)
        task_id = 2
        while True:
            if Task.objects.filter(task_id=task_id).exists():
                break
        res = self.client.post(f"/task/distribute/{task_id}")
        self.assertEqual(res.json()["message"], "Succeed")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        task = Task.objects.get(task_id=task_id)
        # receiver2 and receiver3 with higher credit should be in the tag_user list
        distribute_user_list = set(tag_user.tag_user.user_id for tag_user in task.current_tag_user_list.all())
        self.assertSetEqual(distribute_user_list, {3, 4})

    def test_refuse_task(self):
        res = self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        res = self.client.post("/task/refuse/1")
        task1 = Task.objects.get(task_id=1)
        user2 = User.objects.get(user_name="testReceiver1")
        self.assertTrue(task1.current_tag_user_list.filter(tag_user=user2).exists())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")

    def test_refuse_task_not_receiver(self):
        res = self.client.post("/user/login", {"user_name": "testReceiver2", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        res = self.client.post("/task/refuse/1")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["message"], "no permission to accept")

    def test_get_progress(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get("/task/progress/1", content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"], {"q_id": 1})
        # 做完了题上传答案
        data = {
            "result": [
                "testString",
            ]
        }
        res = self.client.post("/task/upload_res/1/1", data, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        res = self.client.get("/task/progress/1", content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"], {"q_id": 2})

    def test_is_accepted_success(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get("/task/is_accepted/1", content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"], {"is_accepted": True})

    def test_is_distributed_success(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get("/task/is_distributed/1", content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"], {"is_distributed": True})
