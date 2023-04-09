from functools import wraps
from django.http import HttpRequest
from user.models import UserToken
from utils.utils_request import request_failed


def CheckLogin(check_fn):
    @wraps(check_fn)
    def wrap(req: HttpRequest, *args, **kwargs):
        if 'token' not in req.COOKIES or not UserToken.objects.filter(token=req.COOKIES['token']).exists():
            response = request_failed(1001, "not_logged_in", 401)
            response.delete_cookie('token')
            response.delete_cookie('userId')
            return response
        else:
            user = UserToken.objects.get(token=req.COOKIES['token']).user
            return check_fn(req, user, *args, **kwargs)

    return wrap
