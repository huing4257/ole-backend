import json
from django.http import HttpRequest

from utils.utils_check import CheckLogin
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import require, CheckRequire
from user.models import User
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
        if user.score < para["reward_per_q"] * para["distributed_user_num"]:
            return request_failed(10, "score not enough", status_code=400)
        para.update({"publisher": user})
        task = Task.objects.create(**para)
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
            return request_failed(11, "task does not exist", status_code=400)
        elif task.publisher != user:
            return request_failed(12, "no permission to modify", status_code=400)
        else:
            para = require_tasks(req)

            if user.score < para["reward_per_q"] * para["distributed_user_num"]:
                return request_failed(10, "score not enough", status_code=400)

            for key in para:
                setattr(task, key, para[key])
            task.save()
            return request_success({"task_id": task.task_id})

    elif req.method == 'DELETE':
        task = Task.objects.filter(task_id=task_id).first()
        if task is None:
            return request_failed(11, "task does not exist", status_code=400)
        elif task.publisher != user:
            return request_failed(12, "no permission to delete", status_code=403)
        else:
            task.delete()
            return request_success()
    else:
        return BAD_METHOD


@CheckLogin
def get_all_tasks(req: HttpRequest, _user: User):
    if req.method == 'GET':
        tasks = Task.objects.all()
        task_list: list = list()
        for element in tasks:
            task_list.append(element.serialize())
        return request_success(task_list)
    else:
        return BAD_METHOD


@CheckLogin
def get_my_tasks(req: HttpRequest, user: User):
    if req.method == 'GET':
        # 通过cookie判断是否已经登录
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
        return BAD_METHOD


def upload_data():
    pass


def upload_res():
    pass
