import random
from django.test import TestCase
from user.models import User
import bcrypt


class UserTests(TestCase):
    def setUp(self):
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        User.objects.create(
            user_id=1,
            user_name="testUser",
            password=hashed_password.decode("utf-8"),  # store hashed password as a string
            user_type="admin",
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
        return self.client.post("/user/login", payload, content_type="application/json")

    def post_register(self, user_name, password, user_type, invite_code):
        payload = {
            "user_name": user_name,
            "password": password,
            "user_type": user_type,
            "invite_code": invite_code,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.client.post("/user/register", payload, content_type="application/json")

    def post_modify_password(self, old_password, new_password):
        payload = {
            "old_password": old_password,
            "new_password": new_password,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.client.post("/user/modifypassword", payload, content_type="application/json")

    def test_login_success(self):
        user_name = "testUser"
        password = "testPassword"
        res = self.post_login(user_name, password)
        self.assertEqual(res.status_code, 200)

    def test_login_success_cookie(self):
        user_name = "testUser"
        password = "testPassword"
        res = self.post_login(user_name, password)
        self.assertEqual(res.status_code, 200)
        res = self.post_login(user_name, password)
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(res.content, {
            "code": 0,
            "message": "Succeed",
            "data": {"user_id": 1,
                     "user_name": user_name,
                     "user_type": "admin", }

        })

    def test_login_failed1(self):
        user_name = "wrongUser"
        password = "testPassword"
        res = self.post_login(user_name, password)
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"code": 4, "message": "wrong username or password", "data": {}})

    def test_login_failed2(self):
        user_name = "testUser"
        password = "wrongPassword"
        res = self.post_login(user_name, password)
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"code": 4, "message": "wrong username or password", "data": {}})

    def test_logout(self):
        res = self.client.post("/user/logout")
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(res.content, {"code": 0, "message": "Succeed", "data": {}})

    def test_register_success(self):
        user_name: str = "newTestUser"
        password: str = "newPassword"
        user_type: str = random.choice(["admin", "demand", "tag"])
        invite_code: str = "testInviteCode"
        res = self.post_register(user_name, password, user_type, invite_code)
        self.assertEqual(res.status_code, 200)

    def test_register_failed(self):
        user_name: str = "testUser"
        password: str = "newPassword"
        user_type: str = random.choice(["admin", "demand", "tag"])
        invite_code: str = "testInviteCode"
        res = self.post_register(user_name, password, user_type, invite_code)
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"code": 1, "message": "existing username", "data": {}})

    def test_modify_pswd_succeed(self):
        user_name = "testUser"
        password = "testPassword"
        res = self.post_login(user_name, password)
        self.assertEqual(res.status_code, 200)

        oldPassword = "testPassword"
        newPassword = "testNewPassword"
        res2 = self.post_modify_password(oldPassword, newPassword)
        self.assertJSONEqual(res2.content, {
            "code": 0,
            "message": "Succeed",
            "data": {}
        })

    def test_modify_pswd_wrongPswd(self):
        user_name = "testUser"
        password = "testPassword"
        res = self.post_login(user_name, password)
        self.assertEqual(res.status_code, 200)

        oldPassword = "wrongPassword"
        newPassword = "testNewPassword"
        res2 = self.post_modify_password(oldPassword, newPassword)
        self.assertJSONEqual(res2.content, 
                             {
                                 "code": 4,
                                 "message": "wrong password",
                                 "data": {}
                             }
                             )

    def test_modify_pswd_notLogIn(self):
        oldPassword = "wrongPassword"
        newPassword = "testNewPassword"
        res2 = self.post_modify_password(oldPassword, newPassword)
        self.assertEqual(res2.status_code, 401)
        self.assertJSONEqual(res2.content, 
                             {

                                 "code": 1001,
                                 "message": "not_logged_in",
                                 "data": {}

                             }
                             )        

    # userinfo 路由改好后再写测试
    # def test_user_info_failed(self):
    #     res2 = self.client.get(f"/user/userinfo/{9999}")
    #     print(res2.content)
    #     self.assertJSONEqual(res2.content, {
    #         "code": 0,
    #         "message": "succeed",
    #         "data": {
    #             "user_id": 1,
    #             "user_name": "testUser",
    #             "user_type": "admin",
    #             "score": 0,
    #             "membership_level": 0,
    #             "invite_code": "testInviteCode",
    #             "credit_score": 0,
    #             "bank_account": "",
    #             "account_balance": 0,
    #             "grow_value": 0,
    #             "vip_expire_time": 0
    #         }
    #     })

