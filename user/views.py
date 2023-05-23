import json
import string
import secrets

from django.http import HttpRequest

from user.email_views import check_email
from utils.utils_request import request_failed, request_success, BAD_METHOD, return_field
from utils.utils_require import require, CheckRequire
from utils.utils_time import get_timestamp
from utils.utils_check import CheckLogin
from user.models import User, UserToken, BankCard
import bcrypt


@CheckRequire
def register(req: HttpRequest):
    """
    将待注册的用户名和密码作为请求体，后端首先比对是否有重复的用户名，再验证用户名和密码的合法性。若均合法，
    则判断邀请码是否为空，若不为空则查询该邀请码，若存在则给邀请方奖励积分，否则返回错误响应；若邀请码为空
    则跳过这步。最后将加密后的密码、用户名以及生成的不重复邀请码和不重复银行账户一起存储。
    """
    if req.method == "POST":
        body: dict = json.loads(req.body.decode("utf-8"))
        user_name = require(body, "user_name", "string", err_msg="username format error", err_code=2)
        user = User.objects.filter(user_name=user_name).first()
        if user:
            return request_failed(1, "existing username")
        else:
            password = require(body, "password", "string", err_msg="password format error", err_code=3)
            user_type = require(body, "user_type", "string", err_msg="Missing or error type of [userType]")
            assert user_type in ["admin", "demand", "tag", "agent", "advertiser"], "Invalid userType"

            # 检查邀请码的正确性
            invite_code = body.get("invite_code", None)
            if invite_code:
                inviter: User = User.objects.filter(invite_code=invite_code).first()
                if user_type == "admin" and (inviter is None or inviter.user_type != "admin"):
                    return request_failed(80, "need invite code of admin")
                if inviter:
                    inviter.score += 2
                    inviter.save()
                else:
                    return request_failed(92, "wrong invite code")
            elif user_type == "admin":
                return request_failed(80, "need invite code of admin")

            # 检查邮箱验证码
            email = require(body, "email", "string", err_msg="Missing or error type of [email]")
            verifycode = require(body, "verifycode", "string", err_msg="Missing or error type of [verifycode]")
            email_verify_res, email_obj = check_email(email, verifycode)
            if email_verify_res is not None:
                return email_verify_res

            # 生成加密后的密码
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # 生成8位邀请码
            ran_str = ''.join(secrets.SystemRandom(user_name).sample(string.ascii_letters + string.digits, 8))

            user = User(user_name=user_name, password=hashed_password, user_type=user_type, invite_code=ran_str,
                        email=email_obj)
            user.save()
        return request_success(return_field(user.serialize(), ["user_id", "user_name"]))


@CheckLogin
def reset_invite_code(req, _user: User):
    if req.method == "POST":
        ran_str = ''.join(secrets.SystemRandom(_user.user_name).sample(string.ascii_letters + string.digits, 8))
        _user.invite_code = ran_str
        _user.save()
        return request_success()
    else:
        return BAD_METHOD


def login_success(user):
    if user.is_banned:
        return request_failed(1007, "user is banned", 400)
    # 检查会员是否过期
    if user.vip_expire_time < get_timestamp():
        user.membership_level = 0
        user.save()
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


@CheckRequire
def login(req: HttpRequest):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        username = require(body, "user_name", "string", err_msg="invalid request", err_code=1005)
        password = require(body, "password", "string", err_msg="invalid request", err_code=1005)
        user: User = User.objects.filter(user_name=username).first()
        if not user:
            return request_failed(4, "wrong username or password", 400)
        else:
            if bcrypt.checkpw(password.encode('utf-8'), user.password):
                return login_success(user)
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
            to_ban_user: User = User.objects.filter(user_id=user_id).first()
            if to_ban_user is None:
                return request_failed(76, "no such user")
            to_ban_user.is_banned = True
            to_ban_user.save()
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
                return request_failed(1006, "no permission")
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
                            "is_banned": usr.is_banned,
                            "user_type": usr.user_type,
                        }
                    )
                return request_success(user_list)
        elif type == "tag":
            if user.user_type != "admin" and user.user_type != "agent":
                return request_failed(1006, "no permission")
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
def check_user(req: HttpRequest, user: User, user_id: int):
    if req.method == "POST":
        if user.user_type != "admin":
            return request_failed(1006, "no permission")
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
        if user.user_type != "demand":
            return request_failed(1006, "no permission")
        agent_list = list()
        for agent in User.objects.filter(user_type="agent", is_banned=False).all():
            agent_list.append(agent.serialize())
        return request_success({"agent_list": agent_list})
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def withdraw(req: HttpRequest, user: User):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        amount = require(body, "amount", "int", err_msg="Missing or error type of [amount]")
        if user.bank_account is None:
            return request_failed(37, "no bank card")
        if user.score < amount * 15:
            return request_failed(5, "score not enough")
        user.bank_account.card_balance += amount
        user.bank_account.save()
        user.score -= amount * 15
        user.save()
        return request_success()
    else:
        return BAD_METHOD


def get_all_tag_score(req):
    if req.method == "GET":
        ret_data = [return_field(user.serialize(), ["user_id", "user_name", "tag_score", "membership_level"])
                    for user in User.objects.filter(user_type="tag", is_banned=False)]
        return request_success(ret_data)
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def modify_bank_card(req, user: User):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        card_id = require(body, "bank_account", "string", err_msg="Missing or error type of [bank_account]")
        card: BankCard = BankCard.objects.filter(card_id=card_id).first()
        if card is None:
            card = BankCard.objects.create(card_id=card_id, card_balance=secrets.randbelow(114514))
        user.bank_account = card
        user.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def unban_user(req, user: User, user_id):
    if req.method == "POST":
        if user.user_type != "admin":
            return request_failed(19, "no permission")
        else:
            to_ban_user: User = User.objects.filter(user_id=user_id).first()
            if to_ban_user is None:
                return request_failed(76, "no such user")
            to_ban_user.is_banned = False
            to_ban_user.save()
            return request_success()
    else:
        return BAD_METHOD
