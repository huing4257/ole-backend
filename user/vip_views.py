import json

from django.http import HttpRequest

from user.models import User
from utils.utils_check import CheckLogin
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import CheckRequire, require
from utils.utils_time import get_timestamp


def add_grow_value(user: User, add: int):
    """
    给vip用户增加成长值，并更新vip等级
    """
    if user.membership_level == 0:
        return
    user.grow_value += add
    if user.grow_value >= 100:
        user.membership_level = 2
    if user.grow_value >= 1000:
        user.membership_level = 3
    user.save()


@CheckLogin
@CheckRequire
def getvip(req: HttpRequest, user: User):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        package_type = require(body, "package_type", "string", err_msg="username format error", err_code=2)
        if user.membership_level >= 1:
            if package_type == "month":
                if user.score >= 100:
                    user.score -= 100
                    add_grow_value(user, 5)
                    user.vip_expire_time = max(get_timestamp(), user.vip_expire_time) + 15
                    user.save()
                    return request_success()
                else:
                    return request_failed(5, "score not enough")
            elif package_type == "season":
                if user.score >= 250:
                    user.score -= 250
                    add_grow_value(user, 10)
                    user.vip_expire_time = max(get_timestamp(), user.vip_expire_time) + 30
                    user.save()
                    return request_success()
                else:
                    return request_failed(5, "score not enough")
            elif package_type == "year":
                if user.score >= 600:
                    user.score -= 600
                    add_grow_value(user, 15)
                    user.vip_expire_time = max(get_timestamp(), user.vip_expire_time) + 60
                    user.save()
                    return request_success()
                else:
                    return request_failed(5, "score not enough")
        else:
            if package_type == "month":
                if user.score >= 100:
                    user.score -= 100
                    user.membership_level = 1
                    add_grow_value(user, 5)
                    user.vip_expire_time = max(get_timestamp(), user.vip_expire_time) + 15
                    user.save()
                    return request_success()
                else:
                    return request_failed(5, "score not enough")
            elif package_type == "season":
                if user.score >= 250:
                    user.score -= 250
                    user.membership_level = 1
                    add_grow_value(user, 10)
                    user.vip_expire_time = max(get_timestamp(), user.vip_expire_time) + 30
                    user.save()
                    return request_success()
                else:
                    return request_failed(5, "score not enough")
            elif package_type == "year":
                if user.score >= 600:
                    user.score -= 600
                    user.membership_level = 1
                    add_grow_value(user, 15)
                    user.vip_expire_time = max(get_timestamp(), user.vip_expire_time) + 60
                    user.save()
                    return request_success()
                else:
                    return request_failed(5, "score not enough")
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def recharge(req: HttpRequest, user: User):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        amount = require(body, "amount", "int", err_msg="Missing or error type of [amount]")
        if user.bank_account is None:
            return request_failed(37, "no bank card")
        if user.bank_account.card_balance < amount:
            return request_failed(5, "balance not enough")
        add_grow_value(user, amount * 10)
        user.bank_account.card_balance -= amount
        user.bank_account.save()
        user.score += amount * 10
        user.save()
        return request_success()
    else:
        return BAD_METHOD
