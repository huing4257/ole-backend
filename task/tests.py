# Create your tests here.
from django.test import TestCase

from review.models import AnsList, AnsData
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
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        User.objects.create(
            user_id=5,
            user_name="testAdmin",
            password=hashed_password,  # store hashed password as a string
            user_type="admin",
            score=100,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
        )

        tag_list = ["tag1", "tag2", "tag3"]
        for tag in tag_list:
            TagType.objects.create(
                type_name=tag
            )
        tag_type_list = TagType.objects.all()

        self.task = Task.objects.create(
            task_type="text",
            task_style="",
            reward_per_q=0,
            time_limit_per_q=1,
            total_time_limit=1,
            publisher=test_publisher,
            task_id=1,
            distribute_user_num=0,
            task_name="testTask",
            q_num=3,
        )
        self.task.tag_type.set(tag_type_list)
        question1 = Question.objects.create(
            q_id=1,
            data="1",
            data_type="text",
        )
        question1.tag_type.set(tag_type_list)
        question1.save()

        question2 = Question.objects.create(
            q_id=2,
            data="1",
            data_type="text",
        )
        question2.tag_type.set(tag_type_list)
        question2.save()

        question3 = Question.objects.create(
            q_id=3,
            data="1",
            data_type="text",
        )
        question3.tag_type.set(tag_type_list)
        question3.save()

        TextData.objects.create(
            data="string",
            filename="1.txt",
            id=1,
        )

        current_tag_user = Current_tag_user.objects.create(
            tag_user=test_receiver1,
            accepted_at=datetime.datetime.now().timestamp(),
        )
        self.task.current_tag_user_list.add(current_tag_user)
        self.task.past_tag_user_list.add(test_receiver2)
        self.task.questions.add(question1)
        self.task.questions.add(question2)
        self.task.questions.add(question3)
        self.task.publisher = test_publisher

        ans_list = AnsList.objects.create(
            id=1,
        )
        ans_data = AnsData.objects.create(
            filename="1.txt",
            std_ans="test"
        )
        ans_data.save()
        ans_list.ans_list.add(ans_data)
        ans_list.save()
        self.task.ans_list = ans_list

        self.task.save()

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
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["message"], "not_logged_in")

    def test_create_task_success(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        para = self.para.copy()
        para["stdans_tag"] = "1"
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")

    def test_create_task_score_not_enough(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        para = self.para.copy()
        para["reward_per_q"] = 10000000
        res = self.client.post("/task/", para, content_type=default_content_type)
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
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 11)

    def test_modify_task_no_permission(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.put("/task/1", {}, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 12)

    def test_modify_task_distributed(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        self.client.post("/task/distribute/1")
        res = self.client.put("/task/1", {}, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 22)

    def test_modify_task_success(self):
        # 首先创建一个
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        res = self.client.post("/task/", self.para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")

        para2 = self.para.copy()
        para2["task_name"] = "testTask2"
        res2 = self.client.put(f'/task/{res.json()["data"]["task_id"]}', para2, content_type=default_content_type)
        self.assertEqual(res2.status_code, 200)
        self.assertTrue(res2.json()["data"].get("task_id", None))

    def test_modify_task_no_score(self):
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        res = self.client.post("/task/", self.para, content_type=default_content_type)
        para2 = self.para.copy()
        para2["reward_per_q"] = 114514
        res2 = self.client.put(f'/task/{res.json()["data"]["task_id"]}', para2, content_type=default_content_type)
        self.assertEqual(res2.status_code, 400)
        self.assertEqual(res2.json()["code"], 10)

    def test_delete_task_not_logged_in(self):
        res = self.client.delete("/task/1")
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["message"], "not_logged_in")

    def test_delete_task_not_existed(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.delete("/task/10000000003924924")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 11)

    def test_delete_task_no_permission(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.delete("/task/1")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["code"], 12)

    def test_delete_task_success(self):
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        assert res.status_code == 200
        res = self.client.post("/task/", self.para, content_type=default_content_type)
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

    def test_get_task_success_recv(self):
        res = self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        res = self.client.get("/task/1")
        self.assertEqual(res.status_code, 200)

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

    def test_get_my_tasks_recv(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res2 = self.client.get("/task/get_my_tasks")
        self.assertEqual(res2.status_code, 200)

    def test_get_my_tasks_admin(self):
        self.client.post("/user/login", {"user_name": "testAdmin", "password": "testPassword"},
                         content_type=default_content_type)
        res2 = self.client.get("/task/get_my_tasks")
        self.assertEqual(res2.status_code, 400)
        self.assertEqual(res2.json()['code'], 12)

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
        self.task.accept_method = "auto"
        self.task.save()
        res = self.client.post("/task/upload_res/1/1", data, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        res = self.client.post("/task/upload_res/1/2", data, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        res = self.client.post("/task/upload_res/1/3", data, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")

    def test_get_task_question_not_receiver(self):
        self.client.post("/user/login", {"user_name": "testReceiver2", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get(f"/task/{1}/{1}")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["message"], "no access permission")

    def test_get_task_question_receiver(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get(f"/task/{1}/{1}")
        self.assertEqual(res.status_code, 200)

    def test_get_task_question_admin(self):
        self.client.post("/user/login", {"user_name": "testAdmin", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get(f"/task/{1}/{1}")
        self.assertEqual(res.status_code, 200)

    def test_get_task_question_demand(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get(f"/task/{114514}/{1}")
        self.assertEqual(res.status_code, 404)

        res = self.client.get(f"/task/{1}/{114514}")
        self.assertEqual(res.status_code, 404)

        res = self.client.get(f"/task/{1}/{1}")
        self.assertEqual(res.status_code, 200)

    def test_distribute_success(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)

        res = self.client.post("/task/distribute/114514")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()['code'], 14)

        para = self.para.copy()
        para["distribute_user_num"] = 3
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()['data']['task_id']

        res = self.client.post(f"/task/distribute/{task_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        task = Task.objects.get(task_id=task_id)

        distribute_user_list = set(tag_user.tag_user.user_id for tag_user in task.current_tag_user_list.all())
        self.assertEqual(len(distribute_user_list), 3)

    def test_distribute_no_permission(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)

        res = self.client.post("/task/distribute/1")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], 15)

    def test_distribute_no_enough_user(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)

        para = self.para.copy()
        para["distribute_user_num"] = 114
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()['data']['task_id']

        res = self.client.post(f"/task/distribute/{task_id}")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], 21)

    def test_distribute_no_enough_score(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)

        para = self.para.copy()
        para["reward_per_q"] = 20
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id1 = res.json()['data']['task_id']

        para["reward_per_q"] = 20
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()['data']['task_id']

        res = self.client.post(f"/task/distribute/{task_id1}")
        self.assertEqual(res.status_code, 200)
        res = self.client.post(f"/task/distribute/{task_id}")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], 10)

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

    def test_accept_task_no_permission(self):
        self.client.post("/user/login", {"user_name": "testReceiver2", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.post("/task/accept/1")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 18)

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

    def test_get_progress_no_permission(self):
        self.client.post("/user/login", {"user_name": "testReceiver2", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get("/task/progress/1", content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 19)

    def test_is_accepted_success(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get("/task/is_accepted/1", content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"], {"is_accepted": True})

    def test_is_accepted_not_found(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get("/task/is_accepted/114514", content_type=default_content_type)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 14)

    def test_is_accepted_not_distributed_or_not_accept(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)

        para = self.para.copy()
        para["distribute_user_num"] = 3
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()['data']['task_id']

        res = self.client.get(f"/task/is_accepted/{task_id}", content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 22)

        self.client.post(f"/task/distribute/{task_id}")
        res = self.client.get(f"/task/is_accepted/{task_id}", content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"]['is_accepted'], False)

    def test_is_distributed_success_or_not_found(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.get("/task/is_distributed/1", content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"], {"is_distributed": True})

        res = self.client.get("/task/is_distributed/114514", content_type=default_content_type)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 14)

    def test_is_distributed_not_distributed(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)

        para = self.para.copy()
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()['data']['task_id']

        res = self.client.get(f"/task/is_distributed/{task_id}", content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["data"]['is_distributed'], False)

    def test_redistribute(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)

        res = self.client.post("/task/redistribute/114514")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()['code'], 14)

        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 200)

        self.task.current_tag_user_list.first().accept_at = 1
        self.task.save()
        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 200)

        self.task.current_tag_user_list.first().is_finished = True
        self.task.save()
        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 200)

        self.task.current_tag_user_list.first().accept_at = -1
        self.task.save()
        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 200)

        self.task.current_tag_user_list.first().accept_at = None
        self.task.save()
        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 200)

        self.task.distribute_user_num = 114514
        self.task.save()
        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], 21)

        self.task.distribute_user_num = 2
        self.task.save()
        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 200)
