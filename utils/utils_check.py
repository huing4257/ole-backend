from functools import wraps
from django.http import HttpRequest
from user.models import UserToken, User
from utils.utils_request import request_failed


def CheckLogin(check_fn):
    @wraps(check_fn)
    def wrap(req: HttpRequest, *args, **kwargs):
        if 'token' not in req.COOKIES or not UserToken.objects.filter(token=req.COOKIES['token']).exists():
            response = request_failed(1001, "not_logged_in", 401)
            response.delete_cookie('token')
            response.delete_cookie('userId')
            response.delete_cookie('user_type')
            return response
        else:
            user = UserToken.objects.get(token=req.COOKIES['token']).user
            if user.is_banned:
                response = request_failed(1007, "user is banned", 400)
                response.delete_cookie('token')
                response.delete_cookie('userId')
                response.delete_cookie('user_type')
                return response
            return check_fn(req, user, *args, **kwargs)

    return wrap


def CheckUser(check_fn):
    @wraps(check_fn)
    def wrap(req: HttpRequest, user: User, *args, **kwargs):
        if user.user_type == "demand":
            if user.is_checked:
                return check_fn(req, user, *args, **kwargs)
            else:
                return request_failed(35, "user not checked")
        else:
            return check_fn(req, user, *args, **kwargs)

    return wrap
