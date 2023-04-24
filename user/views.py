import json
from django.http import HttpRequest
from utils.utils_request import request_failed, request_success, BAD_METHOD, return_field
from utils.utils_require import require, CheckRequire
from utils.utils_time import get_timestamp
from utils.utils_check import CheckLogin
from user.models import User, UserToken
import bcrypt


@CheckRequire
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


@CheckRequire
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
            if bcrypt.checkpw(password.encode('utf-8'), user.password):
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
                response.set_cookie("token", token, max_age=604800)
                response.set_cookie("userId", user.user_id, max_age=604800)
                response.set_cookie("user_type", user.user_type, max_age=604800)
                return response
            else:
                return request_failed(4, "wrong username or password", 400)
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def logout(req: HttpRequest, _user: User):
    response = request_success()
    user_token = UserToken.objects.get(token=req.COOKIES["token"])
    user_token.delete()
    response.delete_cookie('token')
    response.delete_cookie('userId')
    response.delete_cookie('user_type')
    return response


@CheckLogin
@CheckRequire
def user_info(req: HttpRequest, _user: User, user_id: any):
    user_id = require({"user_id": user_id}, "user_id", "int", err_msg="invalid request", err_code=1005)
    if req.method == "GET":
        user = User.objects.filter(user_id=user_id).first()
        if not user:
            return request_failed(8, "user does not exist", 404)
        if user == _user:
            return request_success(user.serialize(private=True))
        else:
            return request_success(user.serialize())
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def modify_password(req: HttpRequest, user: User):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        old_password = require(body, "old_password", "string", err_msg="Missing or error type of old_password")
        new_password = require(body, "new_password", "string", err_msg="Missing or error type of new_password")
        if bcrypt.checkpw(old_password.encode('utf-8'), user.password):
            user.password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            user.save()
            return request_success()
        else:
            return request_failed(4, "wrong password")
    else:
        return BAD_METHOD


@CheckLogin
def ban_user(req: HttpRequest, user: User, user_id: int):
    if req.method == "POST":
        if user.user_type != "admin":
            return request_failed(19, "no permission")
        else:
            to_ban_user = User.objects.filter(user_id=user_id).first()
            to_ban_user.is_banned = True
            return request_success()
    else:
        return BAD_METHOD


@CheckRequire
@CheckLogin
def get_all_users(req: HttpRequest, user: User):
    if req.method == "GET":
        type = req.GET.get("type")
        if type == "all":
            if user.user_type != "admin":
                return request_failed(19, "no permission")
            else:
                # 查看所有的用户
                user_list: list = list()
                for usr in User.objects.all():
                    user_list.append(
                        {
                            "user_id": usr.user_id,
                            "user_name": usr.user_name,
                            "score": usr.score,
                            "membership_level": usr.membership_level,
                            "credit_score": usr.credit_score,
                            "vip_expire_time": usr.vip_expire_time,
                            "is_checked": usr.is_checked,
                            "is_banned": usr.is_banned
                        }
                    )
                return request_success(user_list)
        elif type == "tag":
            if user.user_type != "admin" and user.user_type != "agent":
                return request_failed(19, "no permission")
            else:
                user_list: list = list()
                # 查看所有的标注方
                for usr in User.objects.filter(user_type="tag").all():
                    user_list.append(
                        {
                            "user_id": usr.user_id,
                            "user_name": usr.user_name,
                            "score": usr.score,
                            "membership_level": usr.membership_level,
                            "credit_score": usr.credit_score,
                            "vip_expire_time": usr.vip_expire_time,
                            "is_checked": usr.is_checked,
                            "is_banned": usr.is_banned
                        }
                    )
                return request_success(user_list)
        else:
            return request_failed(1005, "invalid request")
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def getvip(req: HttpRequest, user: User):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        package_type = require(body, "package_type", "string", err_msg="username format error", err_code=2)
        if user.membership_level >= 1:
            # already vip
            return request_failed(6, "already vip")
        if package_type == "month":
            if user.score >= 100:
                user.score -= 100
                user.membership_level = 1
                user.vip_expire_time = get_timestamp() + 15
                user.save()
                return request_success()
            else:
                return request_failed(5, "score not enough")
        elif package_type == "season":
            if user.score >= 250:
                user.score -= 250
                user.membership_level = 2
                user.vip_expire_time = get_timestamp() + 30
                user.save()
                return request_success()
            else:
                return request_failed(5, "score not enough")
        elif package_type == "year":
            if user.score >= 600:
                user.score -= 600
                user.membership_level = 3
                user.vip_expire_time = get_timestamp() + 60
                user.save()
                return request_success()
            else:
                return request_failed(5, "score not enough")
        else:
            return (1005, "invalid request")
    else:
        return BAD_METHOD


@CheckLogin
def check_user(req: HttpRequest, user: User, user_id: int):
    if req.method == "POST":
        if user.user_type != "admin":
            return request_failed(19, "no permission")
        else:
            target_user = User.objects.filter(user_id=user_id).first()
            target_user.is_checked = True
            target_user.save()
            return request_success()
    else:
        return BAD_METHOD


@CheckLogin
def get_agent_list(req: HttpRequest, user: User):
    if req.method == "GET":
        if user.user_type != "agent":
            return request_failed(19, "no permission")
        else:
            agent_list = list()
            for agent in User.objects.filter(user_type="agent").all():
                agent_list.append(
                    {
                        "user_id": agent.user_id,
                    }
                )
            return request_success(agent_list)
    else:
        return BAD_METHOD
