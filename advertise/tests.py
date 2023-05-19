from django.test import TestCase
from user.models import User, BankCard
from advertise.models import Advertise
import bcrypt
import datetime
default_content_type = "application/json"


class AdvertiseTests(TestCase):
    def setUp(self):
        bankcard = BankCard.objects.create(
            card_id="123456789",
            card_balance=100,
        )
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw("testPassword".encode("utf-8"), salt)
        User.objects.create(
            user_id=1,
            user_name="testAdmin",
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
        User.objects.create(
            user_id=5,
            user_name="testAdvertise",
            password=hashed_password,
            user_type="advertiser",
            score=1000,
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
    
    def test_publish_no_permission(self):
        self.post_login("testTag", "testPassword")
        content = {
            "time": 500,
            "type": 1,
            "url": 1,
        }  
        res = self.client.post("/advertise/publish", content, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {"code": 1006, "message": "no permission", "data": {}}
        )        

    def test_publish_score_not_enough(self):
        self.post_login("testAdvertise", "testPassword")
        content = {
            "time": 100000,
            "type": "horizontal",
            "url": "testURL",
        }
        res = self.client.post("/advertise/publish", content, content_type=default_content_type)   
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {"code": 83, "message": "score not enough", "data": {}}
        )

    def test_publish_success(self):
        self.post_login("testAdvertise", "testPassword")
        content = {
            "time": 500,
            "type": "horizontal",
            "url": "testURL",
        }        
        res = self.client.post("/advertise/publish", content, content_type=default_content_type)   
        self.assertEqual(res.status_code, 200)

    def test_get_ad_no_permission(self):
        self.post_login("testTag", "testPassword")
        res = self.client.get("/advertise/get_ad")
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {"code": 1006, "message": "no permission", "data": {}}
        )              

    def test_get_ad(self):
        self.post_login("testAdvertise", "testPassword")
        res = self.client.get("/advertise/get_ad", {"type": "hotizontal", "num": 3})
        self.assertEqual(res.status_code, 200)

    def test_get_my_ad(self):
        self.post_login("testAdvertise", "testPassword")
        res = self.client.get("/advertise/get_my_ad")
        self.assertEqual(res.status_code, 200)

    def test_renew_not_found(self):
        self.post_login("testAdvertise", "testPassword")
        ad_id = 1
        res = self.client.post(f"/advertise/renew/{ad_id}", {"time": 555}, content_type=default_content_type)
        self.assertEqual(res.status_code, 400)
        self.assertJSONEqual(
            res.content, {"code": 86, "message": "no such ad", "data": {}}
        )

    def test_renew(self):
        self.post_login("testAdvertise", "testPassword")
        content = {
            "time": 500,
            "type": "horizontal",
            "url": "testURL",
        }        
        res = self.client.post("/advertise/publish", content, content_type=default_content_type)   
        self.assertEqual(res.status_code, 200)        
        ad_id = 1
        ad: Advertise = Advertise.objects.filter(ad_id=ad_id).first()
        oldtime = ad.ad_time
        res = self.client.post(f"/advertise/renew/{ad_id}", {"time": 555}, content_type=default_content_type)
        self.assertEqual(res.status_code, 200)
        ad: Advertise = Advertise.objects.filter(ad_id=ad_id).first()
        newtime = ad.ad_time
        self.assertEqual(newtime - oldtime, 555)