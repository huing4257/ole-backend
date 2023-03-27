import json
from django.http import HttpRequest
from utils.utils_request import request_failed, request_success, BAD_METHOD, return_field
from utils.utils_require import require
from utils.utils_time import get_timestamp
from user.models import User, UserToken
import bcrypt


def register(req: HttpRequest):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        user_name = require(body, "user_name", "string", err_msg="username format error", err_code=2)
        user = User.objects.filter(user_name=user_name).first()
        if user:
            return request_failed(1, "existing username")
        else:
            password = require(body, "password", "string", err_msg="username format error", err_code=3)
            user_type = require(body, "user_type", "string", err_msg="Missing or error type of [userType]")
            assert user_type in ["admin", "demand", "tag"], "Invalid userType"
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user = User(user_name=user_name, password=hashed_password, user_type=user_type)
            user.save()
        return request_success(return_field(user.serialize(), ["user_id", "user_name"]))


def login(req: HttpRequest):
    if req.method == "POST":
        # 通过cookie判断是否已经登录
        if "token" in req.COOKIES and UserToken.objects.filter(token=req.COOKIES["token"]).exists():
            user = UserToken.objects.get(token=req.COOKIES["token"]).user
            return_data = {
                "user_id": user.user_id,
                "user_name": user.user_name,
                "user_type": user.user_type,
            }
            return request_success(return_data)

        body = json.loads(req.body.decode("utf-8"))
        username = require(body, "user_name", "string", err_msg="invalid request", err_code=1005)
        password = require(body, "password", "string", err_msg="invalid request", err_code=1005)
        user: User = User.objects.filter(user_name=username).first()
        if not user:
            return request_failed(4, "wrong username or password", 400)
        else:
            if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                return_data = {
                    "user_id": user.user_id,
                    "user_name": user.user_name,
                    "user_type": user.user_type,
                }
                response = request_success(return_data)
                token = bcrypt.hashpw((str(user.user_id) + str(get_timestamp())).encode('utf-8'), bcrypt.gensalt())
                while UserToken.objects.filter(token=token).exists():
                    token = bcrypt.hashpw(((str(user.user_id) + str(get_timestamp())).encode('utf-8')),
                                          bcrypt.gensalt())
                user_token = UserToken(user=user, token=token)
                user_token.save()
                response.set_cookie("token", token)
                return response
            else:
                return request_failed(4, "wrong username or password", 400)
    else:
        return BAD_METHOD


def logout(req: HttpRequest):
    if "token" in req.COOKIES:
        if UserToken.objects.filter(token=req.COOKIES["token"]).exists():
            response = request_success()
            user_token = UserToken.objects.get(token=req.COOKIES["token"])
            user_token.delete()
            response.delete_cookie('token')
            return response
        else:
            return request_failed(1001, "not_logged_in", 401)
    else:
        return request_failed(1001, "not_logged_in", 401)


def user_info(req: HttpRequest, user_id: any):
    user_id = require({"user_id": user_id}, "user_id", "int", err_msg="invalid request", err_code=1005)
    if req.method == "GET":
        if "token" not in req.COOKIES:
            return request_failed(1001, "not_logged_in", 401)

        user = User.objects.filter(user_id=user_id).first()
        if not user:
            return request_failed(8, "user does not exist", 404)
    else:
        return BAD_METHOD


def modify_password(req: HttpRequest):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        if "token" in req.COOKIES:
            user = UserToken.objects.get(token=req.COOKIES["token"]).user
        else:
            return request_failed(1001, "not_logged_in", 401)
        if not user:
            return request_failed(1001, "not_logged_in", 401)
        else:
            old_password = require(body, "old_password", "string", err_msg="Missing or error type of old_password")
            new_password = require(body, "new_password", "string", err_msg="Missing or error type of new_password")
            if bcrypt.checkpw(old_password.encode('utf-8'), user.password.encode('utf-8')):
                user.password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                user.save()
                return request_success()
            else:
                return request_failed(4, "wrong password")
    else:
        return BAD_METHOD
