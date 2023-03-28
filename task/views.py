import json
from django.http import HttpRequest

from utils.utils_check import CheckLogin
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import require, CheckRequire
from user.models import User, UserToken
from task.models import Task


# Create your views here.
@CheckRequire
def require_tasks(req):
    body = json.loads(req.body.decode("utf-8"))
    task_type = require(body, "task_type", "string", err_msg="Missing or error type of [taskType]")
    task_style = require(body, "task_style", "string", err_msg="Missing or error type of [taskStyle]")
    reward_per_q = require(body, "reward_per_q", "int", err_msg="time limit or reward score format error",
                           err_code=9)
    time_limit_per_q = require(body, "time_limit_per_q", "int", err_msg="time limit or reward score format error",
                               err_code=9)
    total_time_limit = require(body, "total_time_limit", "int", err_msg="time limit or reward score format error",
                               err_code=9)
    auto_ac = require(body, "auto_accept", "bool", err_msg="auto accept format error")
    manual_ac = require(body, "manual_accept", "bool", err_msg="manual accept format error")
    return {"task_type": task_type, "task_style": task_style, "reward_per_q": reward_per_q,
            "time_limit_per_q": time_limit_per_q, "total_time_limit": total_time_limit,
            "auto_ac": auto_ac, "manual_ac": manual_ac}


@CheckLogin
def create_task(req: HttpRequest, user: User):
    if req.method == 'POST':
        para = require_tasks(req)
        para.update({"publisher": user})
        task = Task(**para)
        task.save()
        return request_success({"task_id": task.task_id})
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def task_ops(req: HttpRequest, user: User, task_id: any):
    task_id = require({"task_id": task_id}, "task_id", "int", err_msg="Bad param [task_id]", err_code=-1)
    if req.method == 'PUT':
        task = Task.objects.filter(task_id=task_id).first()
        if task is None:
            return request_failed(1, "Task not found", status_code=404)
        elif task.publisher != user:
            return request_failed(1, "You are not the publisher of this task", status_code=403)
        else:
            para = require_tasks(req)
            for key in para:
                setattr(task, key, para[key])
            task.save()
            return request_success({"task_id": task.task_id})


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
                    user.published_list.append(element.serialize())
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
