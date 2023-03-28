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
            data={}
        )

        test_result = Result.objects.create(
            user_id=1,
            result={}
        )
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        test_publisher = User.objects.create(
            user_id=1,
            user_name="testPublisher",
            password=hashed_password,  # store hashed password as a string
            user_type="demand",
            score=0,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
        )
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        test_receiver = User.objects.create(
            user_id=2,
            user_name="testReceiver",
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
            distribute_user_num=1,
        )

        task.data.add(test_data)
        task.distribute_users.add(test_receiver)
        task.result.add(test_result)

    def test(self):
        pass
