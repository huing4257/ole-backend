import json
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
import zipfile
from picbed.models import Image
from utils.utils_check import CheckLogin
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import require, CheckRequire
from utils.utils_time import get_timestamp
from user.models import User, BanUser
from task.models import Task, Result, TextData, Question, Current_tag_user, Progress, TagType
from review.models import AnsList


# Create your views here.

def task_modify_util(req: HttpRequest, task: Task):
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
    # 构建这个task的questions，把数据绑定到每个上
    file_list = require(body, "files", "list", err_msg="Missing or error type of [files]")
    return body, file_list


def require_tasks(req: HttpRequest):
    task = Task.objects.create()
    body, file_list = task_modify_util(req, task)
    tag_type_list = require(body, "tag_type", "list", err_msg="Missing or error type of [tagType]")
    if body["stdans_tag"] != "":
        ans_list = AnsList.objects.filter(id=int(body["stdans_tag"])).first()
        task.ans_list = ans_list
    task.q_num = len(file_list)
    tag_type_list = [TagType.objects.create(type_name=tag) for tag in tag_type_list]
    task.tag_type.set(tag_type_list)
    for q_id, f_id in enumerate(file_list):
        question = Question.objects.create(q_id=q_id + 1, data=f_id, data_type=task.task_type)
        for tag_type in tag_type_list:
            question.tag_type.add(tag_type)
        question.save()
        task.questions.add(question)
    return task


@CheckLogin
def create_task(req: HttpRequest, user: User):
    if req.method == 'POST':
        task: Task = require_tasks(req)
        if user.score < task.reward_per_q * task.q_num * task.distribute_user_num:
            return request_failed(10, "score not enough", status_code=400)
        task.publisher = user
        task.save()
        return request_success({"task_id": task.task_id})
    else:
        return BAD_METHOD


def change_tasks(req: HttpRequest, task: Task):
    _, file_list = task_modify_util(req, task)
    task.q_num = len(file_list)
    for q_id, f_id in enumerate(file_list):
        question = Question(q_id=q_id + 1, data=f_id, data_type=task.task_type)
        question.save()
        task.questions.add(question)
    return task


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
            # 可以修改
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
        ret_data = task.serialize()
        if user.user_type == "tag":
            curr_user: Current_tag_user = task.current_tag_user_list.filter(tag_user=user).first()
            ret_data['accepted_time'] = curr_user.accepted_at
        response = request_success(ret_data)
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
            task_list = []
            for element in published_list:
                task_list.append(element.serialize())
            return request_success(task_list)
        elif user.user_type == "tag":
            all_tasks: list = Task.objects.all()
            distributed_list: list = list()
            for element in all_tasks:
                for current_tag_user in element.current_tag_user_list.all():
                    if user == current_tag_user.tag_user:
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
            flag = True
            i = 1
            for i in range(1, 1 + len(zfile.namelist())):
                filename = f"{i}.txt"
                if filename not in zfile.namelist():
                    flag = False
                    break
                data = zfile.read(f"{i}.txt").decode('utf-8')
                text_data = TextData(data=data, filename=filename)
                text_data.save()
                text_datas.append({
                    "filename": filename,
                    "tag": str(text_data.id),
                })
            if not flag:
                return_data = {
                    "files": text_datas,
                    "upload_num": len(zfile.namelist()),
                    "legal_num": i - 1,
                }
                return request_failed(20, "file sequence interrupt", 200, data=return_data)
            return request_success(text_datas)
        elif data_type == 'image':
            zfile = require(req.FILES, 'file', 'file')
            zfile = zipfile.ZipFile(zfile)
            img_datas = []
            flag = True
            i = 1
            for i in range(1, 1 + len(zfile.namelist())):
                filename = f"{i}.jpg"
                if filename not in zfile.namelist():
                    flag = False
                    break
                data = zfile.read(f"{i}.jpg")
                data_file = SimpleUploadedFile(f"{i}.jpg", data, content_type='image/jpeg')
                img_data = Image(img_file=data_file)
                img_data.filename = filename
                img_data.save()
                img_datas.append({
                    "filename": filename,
                    "tag": str(f"picbed/{img_data.img_file.name}"),
                })
            if not flag:
                return_data = {
                    "files": img_datas,
                    "upload_num": len(zfile.namelist()),
                    "legal_num": i - 1,
                }
                return request_failed(20, "file sequence interrupt", 200, data=return_data)
            return request_success(img_datas)
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def upload_res(req: HttpRequest, user: User, task_id: int, q_id: int):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        result = require(body, "result", "string", err_msg="invalid request", err_code=1005)
        task: Task = Task.objects.filter(task_id=task_id).first()
        # 处理result
        # 上传的是第q_id个问题的结果
        result = Result.objects.create(
            tag_user=user,
            tag_res=result,
        )
        quest: Question = task.questions.filter(q_id=q_id).first()
        quest.result.add(result)
        # 处理progress
        progress: Progress = task.progress.filter(tag_user=user).first()
        if progress:
            # 已经做过这个题目
            # 判断是最后一道题
            if q_id < task.q_num:
                progress.q_id = q_id + 1
            else:
                # 最后一个题已经做完了，就把progress设为0
                progress.q_id = 0
                curr_tag_user: Current_tag_user = task.current_tag_user_list.filter(tag_user=user).first()
                curr_tag_user.is_finished = True
                
                # 开始自动审核
                if task.accept_method == "auto":
                    curr_tag_user.is_check_accepted = "pass"
                    ans_list = task.ans_list
                    questions = task.questions.all()
                    for ans in ans_list.ans_list.all():
                        q_id = int(ans.filename.split('.')[0])
                        question = questions.filter(q_id=q_id).first()
                        result = question.result.all().filter(tag_user=user).first()
                        # print(f"第{q_id}题")
                        # print(f"标注结果{result.tag_res}")
                        # print(f"标准答案{ans.std_ans}")
                        if result.tag_res != ans.std_ans:
                            curr_tag_user.is_check_accepted = "fail"
                    if curr_tag_user.is_check_accepted == "pass":
                        user.score += task.reward_per_q * task.q_num
                        user.save()
                curr_tag_user.save()
            progress.save()
        else:
            # 这个用户还没做过这个题目，创建
            progress: Progress = Progress.objects.create(
                tag_user=user,
                q_id=q_id + 1,
            )
            task.progress.add(progress)
        task.save()
        return request_success()
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
        user_type: str = user.user_type
        if user_type == "demand":
            if release_user_id == user.user_id:
                return_data = question.serialize(detail=True)
                return request_success(return_data)
            else:
                return request_failed(16, "no access permission")
        elif user_type == "tag":
            if task.current_tag_user_list.filter(tag_user=user):
                return_data = question.serialize(detail=True)
                return request_success(return_data)
            else:
                return request_failed(16, "no access permission")
        elif user_type == "admin":
            return_data = question.serialize(detail=True)
            return request_success(return_data)
        else:
            return request_failed(16, "no access permission")
    else:
        return BAD_METHOD


# 分发任务
@CheckLogin
def distribute_task(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        task = Task.objects.filter(task_id=task_id).first()
        if not task:
            return request_failed(14, "task not created")
        if task.publisher != user:
            return request_failed(15, "no distribute permission")
        if task.current_tag_user_list.count() != 0:
            return request_failed(22, "task has been distributed")
        # 顺序分发(根据标注方的信用分从高到低分发)
        tag_users = User.objects.filter(user_type="tag").order_by("-credit_score")
        # 设定的分发用户数比可分发的用户数多
        if task.distribute_user_num > tag_users.count() - BanUser.objects.count():
            return request_failed(21, "tag user not enough")
        
        # 检测分数是否足够 扣分
        if user.score < task.reward_per_q * task.q_num * task.distribute_user_num:
            return request_failed(10, "score not enough")
        else:
            user.score -= task.reward_per_q * task.q_num * task.distribute_user_num
            user.save()
        
        current_tag_user_num = 0  # 当前被分发到的用户数
        for tag_user in tag_users:
            # 检测是否在被封禁用户列表中
            if BanUser.objects.filter(ban_user=tag_user).exists():
                continue
            current_tag_user = Current_tag_user.objects.create(tag_user=tag_user)
            task.current_tag_user_list.add(current_tag_user)
            current_tag_user_num += 1
            if current_tag_user_num >= task.distribute_user_num:
                break
        task.save()
        return request_success()


# 后端收到该请求后，将任务分发给另一个不在past_tag_user_list中的标注用户，并更新current_tag_user_list。若剩余可分发用户不足，则返回错误响应。
@CheckLogin
def refuse_task(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        task = Task.objects.filter(task_id=task_id).first()
        # 顺序分发(根据标注方的信用分从高到低分发)，找到所有的用户
        if task.current_tag_user_list.filter(tag_user=user).exists():
            tag_users = User.objects.filter(user_type="tag").order_by("-credit_score")
            if tag_users.count() > BanUser.objects.all().count() + task.past_tag_user_list.count() + \
                    task.current_tag_user_list.count():
                for tag_user in tag_users:
                    # 检测是否在被封禁用户列表中
                    if BanUser.objects.filter(ban_user=tag_user).exists():
                        continue
                    # 检测是否在过去被分发到的用户列表
                    if task.past_tag_user_list.contains(tag_user):
                        continue
                    # 检测是否在现在的用户列表
                    if task.current_tag_user_list.filter(tag_user=tag_user).exists():
                        continue
                    # tag_user 是新的标注用户，替换到user
                    target: Current_tag_user = task.current_tag_user_list.filter(tag_user=user).first()
                    target.tag_user = tag_user
                    target.accepted_at = get_timestamp()
                    task.past_tag_user_list.add(user)
                    task.save()
                    return request_success()
            else:
                # 没有合适的用户
                return request_failed(17, "available user not enough")
        else:
            # no permission to accept
            return request_failed(18, "no permission to accept")
    else:
        return BAD_METHOD


@CheckLogin
def accept_task(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        task = Task.objects.filter(task_id=task_id).first()
        if task.current_tag_user_list.filter(tag_user=user).exists():
            # current user is tag_user, change accepted_time
            for current_tag_user in task.current_tag_user_list.all():
                if current_tag_user.tag_user == user:
                    current_tag_user.accepted_at = get_timestamp()
                    current_tag_user.save()
            task.save()
            return request_success(task.serialize())
        else:
            # no permission to accept
            return request_failed(18, "no permission to accept")
    else:
        return BAD_METHOD


@CheckLogin
def get_progress(req: HttpRequest, user: User, task_id: int):
    if req.method == "GET":
        task = Task.objects.filter(task_id=task_id).first()
        if task.current_tag_user_list.filter(tag_user=user).exists():
            if task.progress.filter(tag_user=user).first():
                # 已经做过这个题目
                qid = task.progress.filter(tag_user=user).first().q_id
                return request_success({"q_id": qid})
            else:
                # 这个用户还没做过这个题目
                return request_success({"q_id": 1})
        else:
            return request_failed(19, "no access permission")
    else:
        return BAD_METHOD


# 后端判断当前用户是否已经接受任务task_id。
@CheckLogin
def is_accepted(req: HttpRequest, user: User, task_id: int):
    if req.method == "GET":
        task: Task = Task.objects.filter(task_id=task_id).first()
        if not task:
            return request_failed(14, "task not created", 400)
        # 没有分发
        if task.current_tag_user_list.count() == 0:
            return request_failed(22, "task not distributed", 400)
        for current_tag_user in task.current_tag_user_list.all():
            if current_tag_user.tag_user == user and current_tag_user.accepted_at:
                return request_success({"is_accepted": True})
        return request_success({"is_accepted": False})
    else:
        return BAD_METHOD


# 判断请求的任务是否已经被分发
@CheckLogin
def is_distributed(req: HttpRequest, user: User, task_id: int):
    if req.method == "GET":
        task: Task = Task.objects.filter(task_id=task_id).first()
        if not task:
            return request_failed(14, "task not created", 400)
        if task.current_tag_user_list.count() == 0:
            return request_success({"is_distributed": False})
        else:
            return request_success({"is_distributed": True})
    else:
        return BAD_METHOD
