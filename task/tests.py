# Create your tests here.
import os
import zipfile

from django.test import TestCase

from review.models import AnsList, AnsData
from user.models import User, Category
from task.models import Question, CurrentTagUser, Task, TextData, TagType, Progress
import bcrypt
import datetime
from django.core.files.uploadedfile import SimpleUploadedFile

default_content_type = "application/json"


def set_task_checked(task_id):
    task = Task.objects.get(task_id=task_id)
    task.check_result = "accept"
    task.save()


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
        "files": [{'filename': '1.jpg', 'tag': 'picbed/data/picbed/uploads/2023/05/10/1_gE5uYWl.jpg'}, 
                  {'filename': '2.jpg', 'tag': 'picbed/data/picbed/uploads/2023/05/10/2_9S5EAtx.jpg'}, 
                  {'filename': '3.jpg', 'tag': 'picbed/data/picbed/uploads/2023/05/10/3_kme5rxL.jpg'}],
        "tag_type": ["text", "tag2", "tag3"],
        "stdans_tag": "",
        "strategy": "order",
        "input_type": [],
        "cut_num": 0        
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
            is_checked=True
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
        User.objects.create(
            user_id=6,
            user_name="testAgent",
            password=hashed_password,
            user_type="agent",
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

        category_list = ["category1", "category2", "category3"]
        for category in category_list:
            Category.objects.create(
                category=category
            )
        category_type_list = Category.objects.all()

        self.task = Task.objects.create(
            task_type="text",
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
        self.task.task_style.set(category_type_list)
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

        current_tag_user = CurrentTagUser.objects.create(
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
        task = Task.objects.get(task_id=1)
        task_info = task.serialize()
        task_info['current_tag_user_num'] = task.current_tag_user_list.filter(
            state__in=CurrentTagUser.valid_state()
        ).count()
        self.assertEqual(res.json()["data"], task_info)

    def test_get_task_success_recv(self):
        res = self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        res = self.client.get("/task/1")
        self.assertEqual(res.status_code, 200)

    def test_get_all_tasks(self):
        res = self.client.post("/user/login", {"user_name": "testAdmin", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        res = self.client.get("/task/get_all_tasks")
        tasks = Task.objects.all()
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(res.content, {
            "code": 0,
            "message": "Succeed",
            "data": [task.serialize(short=True) for task in tasks]
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

    def test_get_my_tasks_agent(self):
        self.client.post("/user/login", {"user_name": "testAgent", "password": "testPassword"},
                         content_type=default_content_type)
        res2 = self.client.get("/task/get_my_tasks")
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()['code'], 0)    

    def test_upload_textdata(self):
        # 以需求方的身份登录
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        # open file
        if not os.path.exists("./tmp"):
            os.mkdir("./tmp")
        test_zip = zipfile.ZipFile("./tmp/test.zip", 'w', zipfile.ZIP_DEFLATED)
        for i in range(1, 3):
            test_zip.writestr(f"{i}.txt", "test".encode('utf-8'))
        test_zip.writestr(f"{5}.txt", "test".encode('utf-8'))
        test_zip.close()
        with open("./tmp/test.zip", 'rb') as test_zip:
            data = {
                "file": test_zip
            }

            res2 = self.client.post("/task/upload_data?data_type=text", data)
            self.assertEqual(res2.status_code, 200)

            self.assertEqual(res2.json()["message"], "file sequence interrupt")
            self.assertEqual(len(res2.json()["data"]), 3)

    def test_upload_imgdata(self):
        # 以需求方的身份登录
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        # open file
        if not os.path.exists("./tmp"):
            os.mkdir("./tmp")
        test_zip = zipfile.ZipFile("./tmp/test.zip", 'w', zipfile.ZIP_DEFLATED)
        for i in range(1, 3):
            test_zip.writestr(f"{i}.jpg", b"")
        test_zip.writestr(f"{5}.jpg", b"")
        test_zip.close()
        with open("./tmp/test.zip", 'rb') as test_zip:
            data = {
                "file": test_zip
            }

            res2 = self.client.post("/task/upload_data?data_type=image", data)
            self.assertEqual(res2.status_code, 200)

            self.assertEqual(res2.json()["message"], "file sequence interrupt")
            self.assertEqual(len(res2.json()["data"]), 3)

    def test_upload_video(self):
        # 以需求方的身份登录
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        # open file
        if not os.path.exists("./tmp"):
            os.mkdir("./tmp")
        test_zip = zipfile.ZipFile("./tmp/test.zip", 'w', zipfile.ZIP_DEFLATED)
        for i in range(1, 3):
            test_zip.writestr(f"{i}.mp4", b"")
        test_zip.writestr(f"{5}.mp4", b"")
        test_zip.close()
        with open("./tmp/test.zip", 'rb') as test_zip:
            data = {
                "file": test_zip
            }

            res2 = self.client.post("/task/upload_data?data_type=video", data)
            self.assertEqual(res2.status_code, 200)
            self.assertEqual(res2.json()["message"], "file sequence interrupt")
            self.assertEqual(len(res2.json()["data"]), 3)   

    def test_upload_audio(self):
        # 以需求方的身份登录
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        # open file
        if not os.path.exists("./tmp"):
            os.mkdir("./tmp")
        test_zip = zipfile.ZipFile("./tmp/test.zip", 'w', zipfile.ZIP_DEFLATED)
        for i in range(1, 3):
            test_zip.writestr(f"{i}.mp3", b"")
        test_zip.writestr(f"{5}.mp3", b"")
        test_zip.close()
        with open("./tmp/test.zip", 'rb') as test_zip:
            data = {
                "file": test_zip
            }

            res2 = self.client.post("/task/upload_data?data_type=audio", data)
            self.assertEqual(res2.status_code, 200)
            self.assertEqual(res2.json()["message"], "file sequence interrupt")
            self.assertEqual(len(res2.json()["data"]), 3)             

    def test_upload_verify(self):
        # 以需求方的身份登录
        res = self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        # open file
        if not os.path.exists("./tmp"):
            os.mkdir("./tmp")
        test_zip = zipfile.ZipFile("./tmp/test.zip", 'w', zipfile.ZIP_DEFLATED)
        test_zip.writestr("1.txt", b"")
        test_zip.writestr("2.mp3", b"")
        test_zip.writestr("3.mp4", b"")

        test_zip.writestr(f"{5}.jpg", b"")
        test_zip.close()
        with open("./tmp/test.zip", 'rb') as test_zip:
            data = {
                "file": test_zip
            }

            res2 = self.client.post("/task/upload_data?data_type=verify", data)
            self.assertEqual(res2.status_code, 200)
            self.assertEqual(res2.json()["message"], "file sequence interrupt")
            self.assertEqual(len(res2.json()["data"]), 3)                   

    def test_upload_result(self):
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

    def test_upload_result_auto(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)

        para = self.para.copy()
        para["distribute_user_num"] = 3
        para["accept_method"] = "auto"
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()['data']['task_id']

        set_task_checked(task_id)
        res = self.client.post(f"/task/distribute/{task_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        task = Task.objects.get(task_id=task_id)
        prog = Progress(
            tag_user=User.objects.filter(user_id=2).first(),
            q_id=task.q_num
        )
        prog.save()
        task.progress.add(prog)
        task.save()
        distribute_user_list = set(tag_user.tag_user.user_id for tag_user in task.current_tag_user_list.all())
        self.assertEqual(len(distribute_user_list), 3)
        self.client.post("/user/logout")     
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.post(f"/task/accept/{task_id}")
        self.assertEqual(res.status_code, 200)
        data = {
            "result": [
                "testString",
            ]
        }
        q_id = 3
        res = self.client.post(f"/task/upload_res/{task_id}/{q_id}", data, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(res.content, {"code": 0, "message": "Succeed", "data": {}})

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
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {"code": 16, "message": "no access permission", "data": {}}
        )
        self.client.post("/user/logout")
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

        set_task_checked(task_id)
        res = self.client.post(f"/task/distribute/{task_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        task = Task.objects.get(task_id=task_id)

        distribute_user_list = set(tag_user.tag_user.user_id for tag_user in task.current_tag_user_list.all())
        self.assertEqual(len(distribute_user_list), 3)
        self.client.post("/user/logout")
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.post(f"/task/accept/{task_id}")
        self.assertEqual(res.status_code, 200)   
        res = self.client.get(f"/task/{task_id}/{1}")
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

        set_task_checked(task_id)
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

        set_task_checked(task_id)
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

        set_task_checked(task_id1)
        res = self.client.post(f"/task/distribute/{task_id1}")
        self.assertEqual(res.status_code, 200)

        set_task_checked(task_id)
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

    def test_accept_task(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)        
        para = self.para.copy()
        para["distribute_user_num"] = 3
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()['data']['task_id']

        set_task_checked(task_id)
        res = self.client.post(f"/task/distribute/{task_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        task = Task.objects.get(task_id=task_id)

        distribute_user_list = set(tag_user.tag_user.user_id for tag_user in task.current_tag_user_list.all())
        self.assertEqual(len(distribute_user_list), 3)
        self.client.post("/user/logout")
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.post(f"/task/accept/{task_id}")
        self.assertEqual(res.status_code, 200)        

    def test_accept_task_strategy_toall(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)         
        para = self.para.copy()
        para["distribute_user_num"] = 3
        para["strategy"] = "toall"
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()['data']['task_id']
        set_task_checked(task_id)
        res = self.client.post(f"/task/distribute/{task_id}")
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {"code": 22, "message": "task has been distributed", "data": {}}
        )

        self.client.post("/user/logout")
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.post(f"/task/accept/{task_id}")
        self.assertEqual(res.status_code, 200)   
        res = self.client.post(f"/task/accept/{task_id}")
        self.assertEqual(res.status_code, 400) 
        self.assertJSONEqual(
            res.content, {"code": 32, "message": "repeat accept", "data": {}}
        )          

    def test_accept_task_no_permission(self):
        self.client.post("/user/login", {"user_name": "testReceiver2", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.post("/task/accept/1")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 18)

    # def test_get_progress(self):
    #     self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
    #                      content_type=default_content_type)
    #     res = self.client.get("/task/progress/1", content_type=default_content_type)
    #     print(res.content)
    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(res.json()["data"], {"q_id": 1})
    #     # 做完了题上传答案
    #     data = {
    #         "result": [
    #             "testString",
    #         ]
    #     }
    #     res = self.client.post("/task/upload_res/1/1", data, content_type=default_content_type)
    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(res.json()["message"], "Succeed")
    #     res = self.client.get("/task/progress/1", content_type=default_content_type)
    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(res.json()["data"], {"q_id": 2})

    # def test_get_progress_no_permission(self):
    #     self.client.post("/user/login", {"user_name": "testReceiver2", "password": "testPassword"},
    #                      content_type=default_content_type)
    #     res = self.client.get("/task/progress/1", content_type=default_content_type)
    #     self.assertEqual(res.status_code, 400)
    #     self.assertEqual(res.json()["code"], 1006)

    # def test_is_accepted_success(self):
    #     self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
    #                      content_type=default_content_type)
    #     res = self.client.get("/task/is_accepted/1", content_type=default_content_type)
    #     self.assertEqual(res.status_code, 200)
    #     self.assertEqual(res.json()["data"], {"is_accepted": True})

    # def test_is_accepted_not_found(self):
    #     self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
    #                      content_type=default_content_type)
    #     res = self.client.get("/task/is_accepted/114514", content_type=default_content_type)
    #     self.assertEqual(res.status_code, 404)
    #     self.assertEqual(res.json()["code"], 14)

    def test_is_accepted_not_distributed_or_not_accept(self):
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)

        para = self.para.copy()
        para["distribute_user_num"] = 3
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()['data']['task_id']

        # res = self.client.get(f"/task/is_accepted/{task_id}", content_type=default_content_type)
        # self.assertEqual(res.status_code, 400)
        # self.assertEqual(res.json()["code"], 22)

        set_task_checked(task_id)
        self.client.post(f"/task/distribute/{task_id}")
        # res = self.client.get(f"/task/is_accepted/{task_id}", content_type=default_content_type)
        # self.assertEqual(res.status_code, 200)
        # self.assertEqual(res.json()["data"]['is_accepted'], False)

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
        set_task_checked(1)

        res = self.client.post("/task/redistribute/114514")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()['code'], 14)

        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 200)

        self.task.current_tag_user_list.first().accept_at = 1
        self.task.save()
        set_task_checked(1)
        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 200)

        self.task.current_tag_user_list.first().is_finished = True
        self.task.save()
        set_task_checked(1)
        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 200)

        self.task.current_tag_user_list.first().accept_at = -1
        self.task.save()
        set_task_checked(1)
        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 200)

        self.task.current_tag_user_list.first().accept_at = None
        self.task.save()
        set_task_checked(1)
        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 200)

        self.task.distribute_user_num = 114514
        self.task.save()
        set_task_checked(1)
        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()['code'], 21)

        self.task.distribute_user_num = 2
        self.task.save()
        set_task_checked(1)
        res = self.client.post("/task/redistribute/1")
        self.assertEqual(res.status_code, 200)

    def test_to_agent(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        para = self.para.copy()
        para["distribute_user_num"] = 3
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()['data']['task_id']

        res = self.client.post(f"/task/to_agent/{task_id}", {"agent_id": 4}, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.json()["code"], 1006)

        res = self.client.post("/task/to_agent/114514", {"agent_id": 6}, content_type=default_content_type)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.json()["code"], 14)

        res = self.client.post(f"/task/to_agent/{task_id}", {"agent_id": 6}, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task = Task.objects.get(task_id=task_id)
        self.assertEqual(task.agent.user_id, 6)

    def test_distribute_to_user(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        para = self.para.copy()
        res = self.client.post("/task/", para, content_type=default_content_type)
        task_id = res.json()['data']['task_id']

        res = self.client.post(f"/task/to_agent/{task_id}", {"agent_id": 6}, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)

        self.client.post("/user/logout")
        res = self.client.post("/user/login", {"user_name": "testAgent", "password": "testPassword"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)

        res = self.client.post(f"/task/distribute_to_user/{task_id}/{2}", content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        user = User.objects.get(user_id=2)
        self.assertTrue(Task.objects.get(task_id=task_id).current_tag_user_list.filter(tag_user=user).exists())

    def test_get_free_tasks(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)
        # res = self.client.get("/task/get_free_tasks")                              
        # self.assertJSONEqual(res.content, {"code": 1006, "message": "no permission", "data": {}})                
        self.client.post("/user/logout")        
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)  
        res = self.client.get("/task/get_free_tasks")                      
        self.assertJSONEqual(res.content, {"code": 0, "message": "Succeed", "data": []})

    def test_check_task(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)        
        content = {
            "result": "pass",
        }        
        res = self.client.post("/task/check_task/1", content, content_type=default_content_type)        
        self.assertEqual(res.status_code, 400)
        self.client.post("/user/logout")        
        self.client.post("/user/login", {"user_name": "testAdmin", "password": "testPassword"},
                         content_type=default_content_type)
        task_id = 1

        res = self.client.post(f"/task/check_task/{task_id}", content, content_type=default_content_type)
        self.assertJSONEqual(
            res.content,
            {"code": 0, "message": "Succeed", "data": {}}
        )

    def test_taginfo(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)

        para = self.para.copy()
        para["distribute_user_num"] = 3
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()['data']['task_id']

        set_task_checked(task_id)
        res = self.client.post(f"/task/distribute/{task_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        task = Task.objects.get(task_id=task_id)

        distribute_user_list = set(tag_user.tag_user.user_id for tag_user in task.current_tag_user_list.all())
        self.assertEqual(len(distribute_user_list), 3)
        self.client.post("/user/logout")
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.post(f"/task/accept/{task_id}")
        self.assertEqual(res.status_code, 200)  
        # 未上传答案
        res = self.client.get(f"/task/taginfo/{task_id}")
        self.assertEqual(res.status_code, 200)
        # 已上传答案
        data = {
            "result": [
                "testString",
            ]
        }
        self.task.accept_method = "auto"
        self.task.save()
        res = self.client.post(f"/task/upload_res/{task_id}/1", data, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        res = self.client.post(f"/task/upload_res/{task_id}/2", data, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")        

        res = self.client.get(f"/task/taginfo/{task_id}")
        self.assertEqual(res.status_code, 200)

    def test_startquestion(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)

        para = self.para.copy()
        para["distribute_user_num"] = 3
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()['data']['task_id']

        set_task_checked(task_id)
        res = self.client.post(f"/task/distribute/{task_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        task = Task.objects.get(task_id=task_id)

        distribute_user_list = set(tag_user.tag_user.user_id for tag_user in task.current_tag_user_list.all())
        self.assertEqual(len(distribute_user_list), 3)
        self.client.post("/user/logout")     
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.post(f"/task/accept/{task_id}")
        self.assertEqual(res.status_code, 200)           

        q_id = 1 
        res = self.client.post(f"/task/startquestion/{task_id}/{q_id}")
        self.assertEqual(res.status_code, 200)

    def test_upload_many_res(self):
        self.client.post("/user/login", {"user_name": "testPublisher", "password": "testPassword"},
                         content_type=default_content_type)

        para = self.para.copy()
        para["distribute_user_num"] = 3
        res = self.client.post("/task/", para, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()['data']['task_id']

        set_task_checked(task_id)
        res = self.client.post(f"/task/distribute/{task_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["message"], "Succeed")
        task = Task.objects.get(task_id=task_id)

        distribute_user_list = set(tag_user.tag_user.user_id for tag_user in task.current_tag_user_list.all())
        self.assertEqual(len(distribute_user_list), 3)

        self.client.post("/user/logout")     
        self.client.post("/user/login", {"user_name": "testReceiver1", "password": "testPassword"},
                         content_type=default_content_type)
        res = self.client.post(f"/task/accept/{task_id}")
        self.assertEqual(res.status_code, 200)   
        with open("b.csv", "w") as f:
            f.write("filename,tag,tag1,tag2,tag3")
        file = SimpleUploadedFile("b.csv", open("b.csv", "rb").read())
        content = {
            "file": file
        }
        res = self.client.post(f"/task/upload_res/{task_id}", content)
        print(res.content)
        self.assertEqual(res.status_code, 200)                         