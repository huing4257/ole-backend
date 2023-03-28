from functools import wraps

from user.models import UserToken
from utils.utils_request import request_failed


def CheckLogin(check_fn):
    @wraps(check_fn)
    def wrap(req, *args, **kwargs):
        if 'token' not in req.COOKIES or not UserToken.objects.filter(token=req.COOKIES['token']).exists():
            return request_failed(1001, "not_logged_in", 401)
        else:
            user = UserToken.objects.get(token=req.COOKIES['token']).user
            return check_fn(req, user, *args, **kwargs)

    return wrap
