import json
from django.http import HttpRequest

from utils.utils_check import CheckLogin
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import require, CheckRequire
from user.models import User, UserToken
from task.models import Task, Result, Data


# Create your views here.
def require_tasks(req):
    task = Task.objects.create()
    body = json.loads(req.body.decode("utf-8"))
    task.task_type = require(body, "task_type", "string", err_msg="Missing or error type of [taskType]")
    task.task_style = require(body, "task_style", "string", err_msg="Missing or error type of [taskStyle]")
    task.reward_per_q = require(body, "reward_per_q", "int", err_msg="time limit or reward score format error",
                                err_code=9)
    task.time_limit_per_q = require(body, "time_limit_per_q", "int", err_msg="time limit or reward score format error",
                                    err_code=9)
    task.total_time_limit = require(body, "total_time_limit", "int", err_msg="time limit or reward score format error",
                                    err_code=9)
    task.auto_ac = require(body, "auto_ac", "bool", err_msg="auto accept format error")
    task.manual_ac = require(body, "manual_ac", "bool", err_msg="manual accept format error")
    task.distribute_user_num = require(body, "distribute_user_num", "int", err_msg="distribute user num format error")
    return task


@CheckLogin
def create_task(req: HttpRequest, user: User):
    if req.method == 'POST':
        task = require_tasks(req)
        if user.score < task.reward_per_q * task.distribute_user_num:
            return request_failed(10, "score not enough", status_code=400)
        task.publisher = user
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

            if user.score < para["reward_per_q"] * para["distribute_user_num"]:
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
                distributed_list.append(element.serialize())
            return request_success(distributed_list)
        else:
            return request_failed(12, "no task of admin")
    else:
        return BAD_METHOD


@CheckLogin
def upload_data(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        # 通过cookie判断是否已经登录
        body = json.loads(req.body.decode("utf-8"))
        # data is a json list
        data_list = require(body, "data", "list", err_msg="invalid request", err_code=2)
        if not data_list:
            return request_failed(1005, "invalid request")
        else:
            # 判断是否登录
            if "token" in req.COOKIES and UserToken.objects.filter(token=req.COOKIES["token"]).exists():
                task = Task.objects.filter(task_id=task_id).first()
                data = Data.objects.create(
                    data=data_list
                )
                task.data.add(data)
                task.save()
                return request_success()
            else:
                return request_failed(1001, "not_logged_in")
    else:
        return BAD_METHOD


@CheckLogin
def upload_res(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        # 通过cookie判断是否已经登录
        body = json.loads(req.body.decode("utf-8"))
        # RL is a json list
        result_list = require(body, "result", "list", err_msg="invalid request", err_code=2)
        if not result_list:
            return request_failed(1005, "invalid request")
        else:
            # 判断是否登录
            if "token" in req.COOKIES and UserToken.objects.filter(token=req.COOKIES["token"]).exists():
                task = Task.objects.filter(task_id=task_id).first()
                result = Result.objects.create(
                    user_id=user.user_id,
                    result=result_list,
                )
                task.result.add(result)
                task.save()
                return request_success()
            else:
                return request_failed(1001, "not_logged_in")
    else:
        return BAD_METHOD


@CheckLogin
def get_task_question(req: HttpRequest, user: User, task_id: int, q_id: int):
    pass


@CheckLogin
def distribute_task(req: HttpRequest, user: User, task_id: int):
    pass


@CheckLogin
def get_task(req: HttpRequest, user: User, task_id: int):
    pass


@CheckLogin
def refuse_task(req: HttpRequest, user: User, task_id: int):
    pass


@CheckLogin
def accept_task(req: HttpRequest, user: User, task_id: int):
    pass


@CheckLogin
def get_progress(req: HttpRequest, user: User, task_id: int):
    pass