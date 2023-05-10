from django.test import TestCase
from user.models import User
import bcrypt
import datetime

default_content_type = "application/json"


class UserTests(TestCase):
    def setUp(self):
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        User.objects.create(
            user_id=1,
            user_name="testUser",
            password=hashed_password,  # store hashed password as a string
            user_type="admin",
            score=1000,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
            bank_account="testBankAccount",
            account_balance=100,
        )
        User.objects.create(
            user_id=2,
            user_name="testTag",
            password=hashed_password,  # store hashed password as a string
            user_type="tag",
            score=1000,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
        )
        User.objects.create(
            user_id=3,
            user_name="testDemand",
            password=hashed_password,  # store hashed password as a string
            user_type="demand",
            score=1000,
            membership_level=0,
            invite_code="testInviteCode",
        )
        User.objects.create(
            user_id=4,
            user_name="testAgent",
            password=hashed_password,
            user_type="agent",
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
        return self.client.post("/user/login", payload, content_type=default_content_type)

    def post_register(self, user_name, password, user_type, invite_code):
        payload = {
            "user_name": user_name,
            "password": password,
            "user_type": user_type,
            "invite_code": invite_code,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.client.post("/user/register", payload, content_type=default_content_type)

    def post_modify_password(self, old_password, new_password):
        payload = {
            "old_password": old_password,
            "new_password": new_password,
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.client.post("/user/modifypassword", payload, content_type=default_content_type)

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
        user_name = "testUser"
        password = "testPassword"
        self.post_login(user_name, password)
        res = self.client.post("/user/logout")
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(res.content, {"code": 0, "message": "Succeed", "data": {}})

    def test_register_success(self):
        user_name: str = "newTestUser"
        password: str = "newPassword"
        user_type: str = "admin"
        invite_code: str = "testInviteCode"
        res = self.post_register(user_name, password, user_type, invite_code)
        self.assertEqual(res.status_code, 200)

    def test_register_failed(self):
        user_name: str = "testUser"
        password: str = "newPassword"
        user_type: str = "admin"
        invite_code: str = "testInviteCode"
        res = self.post_register(user_name, password, user_type, invite_code)
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"code": 1, "message": "existing username", "data": {}})

    def test_modify_pswd_succeed(self):
        user_name = "testUser"
        password = "testPassword"
        res = self.post_login(user_name, password)
        self.assertEqual(res.status_code, 200)

        old_password = "testPassword"
        new_password = "testNewPassword"
        res2 = self.post_modify_password(old_password, new_password)
        self.assertJSONEqual(res2.content, {
            "code": 0,
            "message": "Succeed",
            "data": {}
        })

    def test_modify_pswd_wrong_pswd(self):
        user_name = "testUser"
        password = "testPassword"
        res = self.post_login(user_name, password)
        self.assertEqual(res.status_code, 200)

        old_password = "wrongPassword"
        new_password = "testNewPassword"
        res2 = self.post_modify_password(old_password, new_password)
        self.assertJSONEqual(res2.content,
                             {
                                 "code": 4,
                                 "message": "wrong password",
                                 "data": {}
                             }
                             )

    def test_modify_pswd_not_login(self):
        old_password = "wrongPassword"
        new_password = "testNewPassword"
        res2 = self.post_modify_password(old_password, new_password)
        self.assertEqual(res2.status_code, 401)
        self.assertJSONEqual(res2.content,
                             {

                                 "code": 1001,
                                 "message": "not_logged_in",
                                 "data": {}

                             }
                             )

    # userinfo 路由改好后再写测试
    def test_user_info_failed(self):
        user_name = "testUser"
        password = "testPassword"
        self.post_login(user_name, password)
        res2 = self.client.get(f"/user/userinfo/{1}")
        self.assertJSONEqual(res2.content, {
            "code": 0,
            "message": "Succeed",
            "data": {
                "user_id": 1,
                "user_name": "testUser",
                "user_type": "admin",
                "score": 1000,
                'is_banned': False,
                'is_checked': False,
                "membership_level": 0,
                "invite_code": "testInviteCode",
                "credit_score": 100,
                "bank_account": "testBankAccount",
                "account_balance": 100,
                "grow_value": 0,
                "vip_expire_time": datetime.datetime.max.timestamp(),
            }   
        })

    def test_ban_user(self):
        user_name = "testUser"
        password = "testPassword"
        self.post_login(user_name, password)
        res = self.client.post(f"/user/ban_user/{2}")
        self.assertEqual(res.status_code, 200)
        res2 = self.client.post("/user/logout")
        self.assertEqual(res2.status_code, 200)
        user_name = "testTag"
        password = "testPassword"
        res = self.post_login(user_name, password)
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"code": 1007, "message": "user is banned", "data": {}})

        user_name = "testDemand"
        self.post_login(user_name, password)
        res3 = self.client.post(f"/user/ban_user/{2}")
        self.assertEqual(res3.status_code, 400)

    def test_get_all_user(self):
        user_name = "testUser"
        password = "testPassword"
        self.post_login(user_name, password)
        res = self.client.get("/user/get_all_users", {"type": "all"})
        self.assertEqual(res.status_code, 200)
        res2 = self.client.get("/user/get_all_users", {"type": "tag"})
        self.assertEqual(res2.status_code, 200)        

    def test_getvip_not_enough(self):
        self.post_login("testAgent", "testPassword")
        res = self.client.post("/user/getvip", {"package_type": "month"}, content_type=default_content_type)
        self.assertJSONEqual(res.content, {"code": 5, "message": "score not enough", "data": {}})
        res3 = self.client.post("/user/getvip", {"package_type": "season"}, content_type=default_content_type)
        self.assertJSONEqual(res3.content, {"code": 5, "message": "score not enough", "data": {}})
        res6 = self.client.post("/user/getvip", {"package_type": "year"}, content_type=default_content_type)
        self.assertJSONEqual(res6.content, {"code": 5, "message": "score not enough", "data": {}})

    def test_getvip_score_success(self):
        self.post_login("testTag", "testPassword")
        res = self.client.post("/user/getvip", {"package_type": "month"}, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        res2 = self.client.post("/user/logout")
        self.assertEqual(res2.status_code, 200)
        
        self.post_login("testUser", "testPassword")
        res3 = self.client.post("/user/getvip", {"package_type": "season"}, content_type=default_content_type)
        self.assertEqual(res3.status_code, 200)
        res4 = self.client.post("/user/logout")
        self.assertEqual(res4.status_code, 200)

        res5 = self.post_login("testDemand", "testPassword")
        self.assertEqual(res5.status_code, 200)
        res6 = self.client.post("/user/getvip", {"package_type": "year"}, content_type=default_content_type)
        self.assertEqual(res6.status_code, 200)   

    def test_check_user(self):
        self.post_login("testUser", "testPassword")
        res = self.client.post(f"/user/check_user/{2}", {"package_typr": "month"}, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)       

    def test_get_agent_list(self):
        self.post_login("testDemand", "testPassword")
        res = self.client.get("/user/get_agent_list")
        self.assertEqual(res.status_code, 200)

    def test_recharge(self):
        self.post_login("testUser", "testPassword")
        res = self.client.post("/user/recharge", {"amount": 10}, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        user = User.objects.filter(user_id=1).first()
        self.assertEqual(user.account_balance, 90)
        res = self.client.post("/user/recharge", {"amount": 1000}, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)

    def test_withdraw(self):
        self.post_login("testUser", "testPassword")
        res = self.client.post("/user/withdraw", {"amount": 10}, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        user = User.objects.filter(user_id=1).first()
        self.assertEqual(user.account_balance, 110)
        res = self.client.post("/user/recharge", {"amount": 1000}, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)        


        