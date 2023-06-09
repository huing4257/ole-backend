from django.test import TestCase
from user.models import User, EmailVerify, BankCard
import bcrypt
import datetime

from user.test_faces import TEST_FACE2, TEST_FACE1

default_content_type = "application/json"


class UserTests(TestCase):
    def setUp(self):
        # face1 and face 2 belong to one person
        self.face1 = TEST_FACE1
        self.face2 = TEST_FACE2
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        EmailVerify.objects.create(
            email="1234@asd.com",
            email_valid="testValid",
            email_valid_expire=datetime.date(2077, 12, 25)
        )
        EmailVerify.objects.create(
            email="new@mail.com",
            email_valid="testValid",
            email_valid_expire=datetime.date(2077, 12, 25)
        )
        bankcard = BankCard.objects.create(
            card_id="123456789",
            card_balance=100,
        )
        User.objects.create(
            user_id=1,
            user_name="testUser",
            password=hashed_password,  # store hashed password as a string
            user_type="admin",
            score=1000,
            membership_level=0,
            invite_code="testInviteCode",
            vip_expire_time=datetime.datetime.max.timestamp(),
            bank_account=bankcard,
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

    def post_register(self, user_name, password, user_type, invite_code, email):
        payload = {
            "user_name": user_name,
            "password": password,
            "user_type": user_type,
            "invite_code": invite_code,
            "email": email,
            "verifycode": "testValid",
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
        email: str = "1234@asd.com"
        res = self.post_register(user_name, password, user_type, invite_code, email)
        self.assertEqual(res.status_code, 200)

    def test_register_failed(self):
        user_name: str = "testUser"
        password: str = "newPassword"
        user_type: str = "admin"
        invite_code: str = "testInviteCode"
        email: str = "1234@asd.com"
        res = self.post_register(user_name, password, user_type, invite_code, email)
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
                "membership_level": 0,
                "invite_code": "testInviteCode",
                "credit_score": 100,
                "bank_account": "123456789",
                "account_balance": 100,
                "grow_value": 0,
                "vip_expire_time": datetime.datetime.max.timestamp(),
                'is_banned': False,
                'is_checked': False,
                "email": "",
                "tag_score": 0,
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

    def test_getvip_score_renewal(self):
        self.post_login("testTag", "testPassword")
        res = self.client.post("/user/getvip", {"package_type": "month"}, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        res3 = self.client.post("/user/getvip", {"package_type": "season"}, content_type=default_content_type)
        self.assertEqual(res3.status_code, 200)
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
        res = self.client.post("/user/recharge", {"amount": 1000}, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)

    def test_withdraw(self):
        self.post_login("testUser", "testPassword")
        res = self.client.post("/user/withdraw", {"amount": 10}, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        res = self.client.post("/user/recharge", {"amount": 1000}, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)

    def test_send_verify_code(self):
        content = {
            "email": "123456@123.com",
        }
        res = self.client.post("/user/get_verifycode", content, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        res = self.client.post("/user/get_verifycode", content, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)

    def test_get_all_tag_scores(self):
        res = self.client.get("/user/get_all_tag_score")
        self.assertEqual(res.status_code, 200)

    def test_modify_bank_card(self):
        self.post_login("testUser", "testPassword")
        res = self.client.post("/user/modifybankaccount", {"bank_account": "123456789"},
                               content_type=default_content_type)
        self.assertEqual(res.status_code, 200)

    def test_change_email(self):
        self.post_login("testUser", "testPassword")
        content = {
            "newemail": "new@mail.com",
            "verifycode": "testValid"
        }
        res = self.client.post("/user/change_email", content, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)

    def test_face_recognition(self):
        self.post_login("testUser", "testPassword")
        content = self.face1
        res = self.client.post("/user/face_recognition", content, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        content2 = self.face2
        res = self.client.post("/user/face_recognition", content2, content_type=default_content_type)
        self.assertEqual(res.status_code, 401)
        self.assertJSONEqual(res.content, {"code": 63, "message": "face registered", "data": {}})

    def test_face_reco_login(self):
        self.post_login("testUser", "testPassword")
        content = self.face1
        res = self.client.post("/user/face_recognition_login", content, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"code": 61, "message": "face unmatched", "data": {}})
        res = self.client.post("/user/face_recognition", content, content_type=default_content_type)
        res = self.client.post("/user/face_recognition_login", content, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)

    def test_verifycode_current_email(self):
        self.post_login("testUser", "testPassword")
        content = {
            "newemail": "new@mail.com",
            "verifycode": "testValid"
        }
        res = self.client.post("/user/change_email", content, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        content2 = {

        }
        res = self.client.post("/user/verifycode_current_email", content2, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(res.content, {"code": 0, "message": "Succeed", "data": {}})

    def test_verifycode_current_email_no_email(self):
        self.post_login("testUser", "testPassword")
        content2 = {

        }
        res = self.client.post("/user/verifycode_current_email", content2, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"code": 52, "message": "no email bound", "data": {}})

    def test_modifypassword_by_email(self):
        self.post_login("testUser", "testPassword")
        content = {
            "newemail": "new@mail.com",
            "verifycode": "testValid"
        }
        res = self.client.post("/user/change_email", content, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        content2 = {
            "verifycode": "testValid",
            "new_password": "newPassword"
        }
        res = self.client.post("/user/modifypassword_by_email", content2, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        self.assertJSONEqual(res.content, {"code": 0, "message": "Succeed", "data": {}})

    def test_modifypassword_by_email_no_email(self):
        self.post_login("testUser", "testPassword")
        content2 = {}
        res = self.client.post("/user/modifypassword_by_email", content2, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(res.content, {"code": 52, "message": "no email bound", "data": {}})

    def test_reset_invite_code(self):
        self.post_login("testUser", "testPassword")
        res = self.client.post("/user/reset_invite_code", {}, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)

    def test_unban_user_no_permission(self):
        self.post_login("testTag", "testPassword")
        res = self.client.post(f"/user/unban_user/{1}", {}, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {'code': 19, 'data': {}, 'message': 'no permission'}
        )

    def test_unban_user(self):
        self.post_login("testUser", "testPassword")
        res = self.client.post(f"/user/unban_user/{3}", {}, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)

    def test_unban_user_not_found(self):
        self.post_login("testUser", "testPassword")
        res = self.client.post(f"/user/unban_user/{30000}", {}, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {'code': 76, 'data': {}, 'message': 'no such user'}
        )
