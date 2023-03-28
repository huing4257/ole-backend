import json
from django.http import HttpRequest
from utils.utils_request import request_failed, request_success, BAD_METHOD, return_field
from utils.utils_require import require, CheckRequire
from utils.utils_time import get_timestamp
from user.models import User, UserToken
from task.models import Task
import bcrypt


# Create your views here.
def task_init():
    pass


def task_ops():
    pass


def all():
    pass


def get_my_tasks(req: HttpRequest):
    if req.method == 'GET':
        # 通过cookie判断是否已经登录
        if "token" in req.COOKIES and UserToken.objects.filter(token=req.COOKIES["token"]).exists():
            user = UserToken.objects.get(token=req.COOKIES["token"]).user
            if user.user_type == "demand":
                published = user.published_task.all()
                published_list: list = list()
                for element in published:
                    published_list.append(element.serialize())
                return request_success(published_list)
            elif user.user_type == "tag":
                distributed = user.distributed_tasks.all()
                distributed_list: list = list()
                for element in distributed:
                    published_list.append(element.serialize())
                return request_success(distributed_list)
            else:
                return request_failed(12, "no task of admin")
        else:
            return request_failed(1001, "not_logged_in")

    else:
        return BAD_METHOD


def upload_data():
    pass


def upload_res():
    pass