import base64
import datetime
import json
import secrets
from pathlib import Path

import bcrypt
from django.core.mail import send_mail

from user.models import User, EmailVerify
from utils.utils_check import CheckLogin
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import CheckRequire, require


@CheckRequire
def send_verify_code(req):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        email = require(body, "email", "string", err_msg="Missing or error type of [email]")

        # 邮箱已被绑定
        if User.objects.filter(email__email=email).exists():
            return request_failed(41, "email already bound")

        with open(Path(__file__).resolve().parent / "imgs" / "blue_archive.png", "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")
        valid_code = str(secrets.randbelow(999999)).zfill(6)
        message = f"您的注册验证码是<br>" \
                  f"<h1>{valid_code}</h1>" \
                  f"验证码 1 分钟有效，过期请重新获取。<br><br>" \
                  f"如果这不是您发起的请求，请忽略此邮件。<br>" \
                  f'<img width=210px height=100px src="data:image/png ;base64,{img_base64}"/>'
        send_success = send_mail("关注永雏塔菲喵 关注永雏塔菲谢谢喵",
                                 "",
                                 "ole@blog.xial.moe",
                                 [email],
                                 html_message=message)

        # 发送邮件失败
        if send_success == 0:
            return request_failed(40, "send verify code failed")

        # 更新数据库中 Verify Code & Expire Time
        email_obj: EmailVerify = EmailVerify.objects.filter(email=email).first()
        if email_obj is None:
            EmailVerify.objects.create(email=email,
                                       email_valid=valid_code,
                                       email_valid_expire=datetime.datetime.now() + datetime.timedelta(minutes=5))
        else:
            email_obj.email_valid = valid_code
            email_obj.email_valid_expire = datetime.datetime.now() + datetime.timedelta(minutes=1)
            email_obj.save()

        return request_success()

    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def change_email(req, user: User):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))

        # 检查邮箱验证码
        email = require(body, "newemail", "string", err_msg="Missing or error type of [newemail]")
        verifycode = require(body, "verifycode", "string", err_msg="Missing or error type of [verifycode]")
        email_verify_res, email_obj = check_email(email, verifycode, check_exist=True)
        if email_verify_res is not None:
            return email_verify_res

        user.email = email_obj
        user.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def verifycode_current_email(req, user: User):
    if req.method == "POST":
        email_obj: EmailVerify = user.email
        if email_obj is None:
            return request_failed(52, "no email bound")
        email = email_obj.email
        with open(Path(__file__).resolve().parent / "imgs" / "blue_archive.png", "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")
        valid_code = str(secrets.randbelow(999999)).zfill(6)
        message = f"您的验证码是<br>" \
                  f"<h1>{valid_code}</h1>" \
                  f"验证码 1 分钟有效，过期请重新获取。<br><br>" \
                  f"如果这不是您发起的请求，请忽略此邮件。<br>" \
                  f'<img width=210px height=100px src="data:image/png ;base64,{img_base64}"/>'
        send_success = send_mail("关注永雏塔菲喵 关注永雏塔菲谢谢喵",
                                 "",
                                 "ole@blog.xial.moe",
                                 [email],
                                 html_message=message)

        # 发送邮件失败
        if send_success == 0:
            return request_failed(40, "send verify code failed")

        # 更新数据库中 Verify Code & Expire Time
        email_obj.email_valid = valid_code
        email_obj.email_valid_expire = datetime.datetime.now() + datetime.timedelta(minutes=1)
        email_obj.save()

        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
def modifypassword_by_email(req, user: User):
    if req.method == "POST":
        email_obj: EmailVerify = user.email
        if email_obj is None:
            return request_failed(52, "no email bound")
        body = json.loads(req.body.decode("utf-8"))
        verifycode = require(body, "verifycode", "string", err_msg="Missing or error type of [verifycode]")
        new_password = require(body, "new_password", "string", err_msg="Missing or error type of [new_password]")
        email_verify_res, _ = check_email(email_obj.email, verifycode)
        if email_verify_res is not None:
            return email_verify_res
        user.password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        user.save()
        return request_success()
    else:
        return BAD_METHOD


def check_email(email, verifycode, check_exist: bool = False):
    """
    检查邮箱验证码的正确性
    """
    email_obj: EmailVerify = EmailVerify.objects.filter(email=email, email_valid=verifycode).filter().first()
    if email_obj is None:
        return request_failed(46, "wrong email verify code"), None
    if email_obj.email_valid_expire < datetime.datetime.now().replace(tzinfo=datetime.timezone.utc):
        return request_failed(45, "email verify code expired"), None

    if User.objects.filter(email__email=email).exists() and check_exist:
        return request_failed(41, "email already bound"), None
    return None, email_obj
