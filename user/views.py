import json
from django.http import HttpRequest
from utils.utils_request import request_failed, request_success, return_field
from utils.utils_require import require
from user.models import User
import bcrypt


def register(req: HttpRequest):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))

        user_name = require(body, "userName", "string", err_msg="username format error", err_code=2)
        user = User.objects.filter(name=user_name).first()

        if user:
            return request_failed(1, "existing username")
        else:
            password = require(body, "password", "string", err_msg="username format error", err_code=3)

            user_type = require(body, "userType", "string", err_msg="Missing or error type of [userType]")
            assert user_type in ["admin", "demand", "tag"], "Invalid userType"

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            user = User(name=user_name, password=hashed_password, user_type=user_type)
            user.save()

        return request_success(return_field(user.serialize(), ["user_id", "user_name"]))


def login(req: HttpRequest):
    return None
