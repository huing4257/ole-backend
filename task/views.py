import json
from django.http import HttpRequest
import zipfile
from utils.utils_check import CheckLogin
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import require, CheckRequire
from user.models import User, UserToken
from task.models import Task, Result, TextData, Question


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
    task.distribute_user_num = require(body, "distribute_user_num", "int", err_msg="distribute user num format error")
    task.task_name = require(body, "task_name", "string", err_msg="Missing or error type of [taskName]")
    task.accept_method = require(body, "accept_method", "string", err_msg="Missing or error type of [acceptMethod]")
    return task


@CheckLogin
def create_task(req: HttpRequest, user: User):
    if req.method == 'POST':
        task = require_tasks(req)
        if user.score < task.reward_per_q * task.distribute_user_num:
            return request_failed(10, "score not enough", status_code=400)
        task.publisher = user
        body = json.loads(req.body.decode("utf-8"))
        file_list = require(body, "files", "list", err_msg="Missing or error type of [files]")
        task.q_num = len(file_list)
        for f_id in file_list:
            # 构建这个task的questions，把数据绑定到每个上
            question = Question(data=f_id, data_type=task.task_type)
            question.save()
            task.questions.add(question)
        task.save()
        return request_success({"task_id": task.task_id})
    else:
        return BAD_METHOD


@CheckLogin
# @CheckRequire
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
    elif req.method == 'GET':
        task = Task.objects.filter(task_id=task_id).first()
        if not task:
            return request_failed(11, "task does not exist", 404)
        response = request_success(task.serialize())
        response.set_cookie("user_type", user.user_type)
        return response
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
            published_list = Task.objects.filter(publisher=user).all()
            published = user.published_task.all()
            published_list: list = list()
            for element in published:
                published_list.append(element.serialize())
            return request_success(published_list)
        elif user.user_type == "tag":
            all_tasks: list = Task.objects.all()
            distributed_list: list = list()
            for element in all_tasks:
                if user in element.current_tag_user_list():
                    distributed_list.append(element.serialize())
            return request_success(distributed_list)
        else:
            return request_failed(12, "no task of admin")
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def upload_data(req: HttpRequest, user: User):
    # 上传一个压缩包，根目录下有 x.txt/x.jpg x为连续自然数字
    if req.method == "POST":
        data_type = require(req.GET, "data_type")
        if data_type == 'text':
            zfile = require(req.FILES, 'file', 'file')
            zfile = zipfile.ZipFile(zfile)
            text_datas = []
            for i in range(1, 1 + len(zfile.namelist())):
                filename = f"{i}.txt"
                if filename not in zfile.namelist():
                    break
                data = zfile.read(f"{i}.txt").decode('utf-8')
                text_data = TextData(data=data, filename=filename)
                text_data.save()
                text_datas.append({
                    "filename": filename,
                    "tag": str(text_data.id),
                })
            return request_success(text_datas)
        elif data_type == 'image':
            pass
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
def upload_res(req: HttpRequest, user: User, task_id: int, q_id: int):
    if req.method == "POST":
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
    if req.method == "GET":
        # 找到task 和 question
        task = Task.objects.filter(task_id=task_id).first()
        if not task:
            return request_failed(11, "task does not exist")
        question = task.questions.filter(q_id=q_id).first()
        if not question:
            return request_failed(13, "question does not exist")
        release_user_id = task.publisher.user_id
        type: str = user.user_type
        if type == "demand":
            if release_user_id == user.user_id:
                return_data = question.serialize()
                return request_success(return_data)
            else:
                return request_failed(16, "no access permission")
        elif type == "tag":
            if task.current_tag_user_list.filter(tag_user=user):
                return_data = question.serialize()
                return request_success(return_data)
            else:
                return request_failed(16, "no access permission")
        elif type == "admin":
            return_data = question.serialize()
            return request_success(return_data)
        else:
            return request_failed(16, "no access permission")
    else:
        return BAD_METHOD


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
