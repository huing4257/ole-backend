import json
from django.http import HttpRequest

from task.distribute_views import update_task_tagger_list
from utils.utils_check import CheckLogin, CheckUser
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import require, CheckRequire
from user.models import User, Category, UserCategory
from task.models import Task, Question, CurrentTagUser, TagType, InputType
from review.models import AnsList
from django.db.models import IntegerField, Value


# Create your views here.

@CheckLogin
@CheckUser
def create_task(req: HttpRequest, user: User):
    if req.method == 'POST':
        task = Task.objects.create(publisher=user)
        task = change_tasks(req, task)
        if user.score < task.reward_per_q * task.q_num * task.distribute_user_num:
            return request_failed(10, "score not enough", status_code=400)
        task.save()
        return request_success({"task_id": task.task_id})
    else:
        return BAD_METHOD


def change_tasks(req: HttpRequest, task: Task):
    """
    用于从请求体中读取数据修改任务信息的函数
    """
    body = json.loads(req.body.decode("utf-8"))
    # 捕获任务样式中的内容并分割成词
    task_style = require(body, "task_style", "string", err_msg="Missing or error type of [taskStyle]")
    for _category in task_style.split(' '):
        if _category:
            category, created = Category.objects.get_or_create(category=_category)
            task.task_style.add(category)
    # 修改
    task.task_type = require(body, "task_type", "string", err_msg="Missing or error type of [taskType]")
    task.reward_per_q = require(body, "reward_per_q", "int", err_msg="time limit or reward score format error",
                                err_code=9)
    task.time_limit_per_q = require(body, "time_limit_per_q", "int", err_msg="time limit or reward score format error",
                                    err_code=9)
    task.total_time_limit = require(body, "total_time_limit", "int", err_msg="time limit or reward score format error",
                                    err_code=9)
    task.distribute_user_num = require(body, "distribute_user_num", "int", err_msg="distribute user num format error")
    task.task_name = require(body, "task_name", "string", err_msg="Missing or error type of [taskName]")
    task.accept_method = require(body, "accept_method", "string", err_msg="Missing or error type of [acceptMethod]")
    task.strategy = require(body, "strategy", "string", err_msg="Missing or error type of [strategy]")

    # 获取 input_type list
    input_type_list = require(body, "input_type", "list", err_msg="Missing or error type of [input_type]")
    input_type_obj_list = [InputType.objects.create(input_tip=input_tip) for input_tip in input_type_list]
    task.input_type.set(input_type_obj_list)

    # 获取 cut_num
    task.cut_num = require(body, "cut_num", 'int', err_msg="Missing or error type of [cut_num]")

    # 获取 tag_type list
    tag_type_list = require(body, "tag_type", "list", err_msg="Missing or error type of [tagType]")
    tag_type_obj_list = [TagType.objects.create(type_name=tag) for tag in tag_type_list]
    task.tag_type.set(tag_type_obj_list)

    # 获取 ans_list
    if body["stdans_tag"] != "":
        ans_list = AnsList.objects.filter(id=int(body["stdans_tag"])).first()
        task.ans_list = ans_list

    # 构建这个task的questions，把数据绑定到每个上
    file_list = require(body, "files", "list", err_msg="Missing or error type of [files]")
    task.q_num = len(file_list)
    for q_id, file in enumerate(file_list):
        f_id = file['tag']
        filename = file['filename']
        if filename[-4:] == ".txt":
            data_type = "text"
        elif filename[-4:] == ".jpg":
            data_type = "image"
        elif filename[-4:] == ".mp4":
            data_type = "video"
        elif filename[-4:] == ".mp3":
            data_type = "audio"
        else:
            data_type = "text"
        question = Question.objects.create(q_id=q_id + 1, data=f_id, data_type=data_type, cut_num=task.cut_num)
        question.tag_type.set(tag_type_obj_list)
        question.cut_num = task.cut_num
        question.input_type.set(input_type_obj_list)
        question.save()
        task.questions.add(question)
    task.save()
    return task


@CheckLogin
@CheckUser
@CheckRequire
def task_ops(req: HttpRequest, user: User, task_id: any):
    task_id = require({"task_id": task_id}, "task_id", "int", err_msg="Bad param [task_id]", err_code=-1)

    if req.method == 'PUT':
        task = Task.objects.filter(task_id=task_id).first()
        if task is None:
            return request_failed(11, "task does not exist", status_code=404)
        elif task.publisher != user:
            return request_failed(12, "no permission to modify", status_code=400)
        elif task.current_tag_user_list.count() != 0:
            return request_failed(22, "task has been distributed")
        else:
            # 可以修改
            task.questions.set([])
            task.task_style.set([])
            task.save()
            change_tasks(req, task)
            if user.score < task.reward_per_q * task.distribute_user_num:
                return request_failed(10, "score not enough", status_code=400)
            # for key in para:
            #     setattr(task, key, para[key])
            task.save()
            return request_success({"task_id": task.task_id})

    elif req.method == 'DELETE':
        task = Task.objects.filter(task_id=task_id).first()
        if task is None:
            return request_failed(11, "task does not exist", status_code=404)
        elif task.publisher != user:
            return request_failed(12, "no permission to delete", status_code=403)
        else:
            task.delete()
            return request_success()
    elif req.method == 'GET':
        task: Task = Task.objects.filter(task_id=task_id).first()
        # for category in task.task_style.all():
        #     print(category.category)
        if not task:
            return request_failed(11, "task does not exist", 404)
        ret_data = task.serialize()
        if user.user_type == "tag":
            curr_user: CurrentTagUser = task.current_tag_user_list.filter(tag_user=user).first()
            ret_data['current_tag_user_list'] = []
            if curr_user:
                ret_data['accepted_time'] = curr_user.accepted_at
                ret_data['current_tag_user_list'].append(curr_user.serialize())
        ret_data['current_tag_user_num'] = task.current_tag_user_list.filter(
            state__in=CurrentTagUser.valid_state()
        ).count()
        response = request_success(ret_data)
        response.set_cookie("user_type", user.user_type)
        return response
    else:
        return BAD_METHOD


@CheckLogin
@CheckUser
def get_all_tasks(req: HttpRequest, user: User):
    if req.method == 'GET':
        if user.user_type != "admin":
            return request_failed(1006, "no permission", status_code=400)
        tasks = Task.objects.all()
        task_list: list = list()
        for element in tasks:
            task_list.append(element.serialize(short=True))
        return request_success(task_list)
    else:
        return BAD_METHOD


@CheckLogin
@CheckUser
def get_my_tasks(req: HttpRequest, user: User):
    if req.method == 'GET':
        if user.user_type == "demand":
            published_list = Task.objects.filter(publisher=user).all()
            distribute_list = []
            undistribute_list = []
            for element in published_list:
                if element.current_tag_user_list.count():
                    distribute_list.append(element.serialize())
                else:
                    undistribute_list.append(element.serialize())
            distribute_list.reverse()
            return request_success(undistribute_list + distribute_list)
        elif user.user_type == "tag":
            all_tasks: list[Task] = Task.objects.all()
            task_list = []
            for element in all_tasks:
                current_tag_user: CurrentTagUser = element.current_tag_user_list.filter(tag_user=user).first()
                if current_tag_user:
                    if current_tag_user.state != "refused":
                        task_list.append(element.serialize())
                        task_list[-1]["state"] = current_tag_user.state
            return request_success(task_list)
        elif user.user_type == "agent":
            all_tasks = user.hand_out_task.all()
            return_list = list()
            for element in all_tasks:
                task: Task = element
                update_task_tagger_list(task)
                current_tag_user_num = task.current_tag_user_list.filter(
                    state__in=CurrentTagUser.valid_state()
                ).count()
                ret_task = task.serialize(short=True)
                ret_task.update({"current_tag_user_num": current_tag_user_num})
                return_list.append(ret_task)
            return request_success(return_list)
        else:
            return request_failed(12, "no task of admin")
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def get_free_tasks(req: HttpRequest, user: User):
    if req.method == "GET":
        usercategories = UserCategory.objects.filter(user=user).all()
        categories = user.categories.all()
        tasks = Task.objects.filter(strategy="toall", check_result="accept", task_style__in=categories). \
            distinct().annotate(my_count=Value(0, output_field=IntegerField()))
        for task in tasks:
            for category in task.task_style.all():
                usercategory = usercategories.filter(category=category).first()
                if usercategory:
                    task.my_count += usercategory.count
        tasks = list(tasks)
        tasks.sort(key=lambda task: -task.my_count)
        left_tasks = Task.objects.filter(strategy="toall", check_result="accept").exclude(task_style__in=categories)
        return_list = [element.serialize() for element in tasks if
                       element.current_tag_user_list.filter(
                           state__in=CurrentTagUser.valid_state()
                       ).count() < element.distribute_user_num] + \
                      [element.serialize() for element in left_tasks if
                       element.current_tag_user_list.filter(
                           state__in=CurrentTagUser.valid_state()
                       ).count() < element.distribute_user_num]
        return request_success(return_list)
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def check_task(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        if user.user_type != "admin":
            return request_failed(16, "no permission")
        body = json.loads(req.body.decode("utf-8"))
        check_result = require(body, "result", "string", err_msg="invalid request", err_code=1005)
        task = Task.objects.filter(task_id=task_id).first()
        if task.check_result == "wait":
            task.check_result = check_result
        else:
            return request_failed(51, "recheck")
        task.save()
        return request_success()
    else:
        return BAD_METHOD
