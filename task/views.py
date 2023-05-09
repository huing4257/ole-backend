import json
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpRequest
import zipfile
from picbed.models import Image
from utils.utils_check import CheckLogin, CheckUser
from utils.utils_request import request_failed, request_success, BAD_METHOD
from utils.utils_require import require, CheckRequire
from utils.utils_time import get_timestamp, DAY
from user.models import User, Category, UserCategory
from user.views import add_grow_value
from task.models import Task, Result, TextData, Question, CurrentTagUser, Progress, TagType, InputType
from review.models import AnsList
from django.core.cache import cache
from django.db.models import Q, IntegerField, Value

from video.models import Video


# Create your views here.

@CheckLogin
@CheckUser
def create_task(req: HttpRequest, user: User):
    if req.method == 'POST':
        task = Task.objects.create()
        task = change_tasks(req, task)
        if user.score < task.reward_per_q * task.q_num * task.distribute_user_num:
            return request_failed(10, "score not enough", status_code=400)
        task.publisher = user
        task.save()
        return request_success({"task_id": task.task_id})
    else:
        return BAD_METHOD


# 用于从请求体中读取数据修改任务信息的函数
def change_tasks(req: HttpRequest, task: Task):
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
    # 构建这个task的questions，把数据绑定到每个上
    file_list = require(body, "files", "list", err_msg="Missing or error type of [files]")
    tag_type_list = require(body, "tag_type", "list", err_msg="Missing or error type of [tagType]")
    if body["stdans_tag"] != "":
        ans_list = AnsList.objects.filter(id=int(body["stdans_tag"])).first()
        task.ans_list = ans_list
    task.q_num = len(file_list)
    tag_type_list = [TagType.objects.create(type_name=tag) for tag in tag_type_list]
    task.tag_type.set(tag_type_list)
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
        question = Question.objects.create(q_id=q_id + 1, data=f_id, data_type=data_type)
        for tag_type in tag_type_list:
            question.tag_type.add(tag_type)
        question.save()
        task.questions.add(question)
    # 获取 input_type list
    input_type_list = require(body, "input_type", "list", err_msg="Missing or error type of [input_type]")
    for input_type in input_type_list:
        tmp_input_type = InputType(input_type)
        tmp_input_type.save()
        task.input_type.add(tmp_input_type)
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
        task = Task.objects.filter(task_id=task_id).first()
        # for category in task.task_style.all():
        #     print(category.category)
        if not task:
            return request_failed(11, "task does not exist", 404)
        ret_data = task.serialize()
        if user.user_type == "tag":
            curr_user: CurrentTagUser = task.current_tag_user_list.filter(tag_user=user).first()
            if curr_user:
                ret_data['accepted_time'] = curr_user.accepted_at
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
            all_tasks: list = Task.objects.all()
            unfinish_list = []
            finish_list = []
            for element in all_tasks:
                for current_tag_user in element.current_tag_user_list.all():
                    if user == current_tag_user.tag_user:
                        if current_tag_user.accepted_at and current_tag_user.accepted_at == -1:
                            continue
                        if current_tag_user.is_finished:
                            finish_list.append(element.serialize())
                        else:
                            unfinish_list.append(element.serialize())
            finish_list.reverse()
            return request_success(unfinish_list + finish_list)
        elif user.user_type == "agent":
            all_tasks = user.hand_out_task.all()
            return_list = list()
            for element in all_tasks:
                task: Task = element
                update_task_tagger_list(task)
                current_tag_user_num = task.current_tag_user_list.count()
                ret_task = task.serialize(short=True)
                ret_task.update({"current_tag_user_num": current_tag_user_num})
                return_list.append(ret_task)
            return request_success(return_list)
        else:
            return request_failed(12, "no task of admin")
    else:
        return BAD_METHOD


def create_text_data(data, filename):
    text_data = TextData(data=data, filename=filename)
    text_data.save()
    return {
        "filename": filename,
        "tag": str(text_data.id),
    }


def create_image_data(data, filename):
    data_file = SimpleUploadedFile(filename, data, content_type='image/jpeg')
    img_data = Image(img_file=data_file, filename=filename)
    img_data.save()
    return {
        "filename": filename,
        "tag": str(f"picbed/{img_data.img_file.name}"),
    }


def create_video_data(data, filename):
    data_file = SimpleUploadedFile(filename, data, content_type='video/mp4')
    vid_data = Video(video_file=data_file, filename=filename)
    vid_data.save()
    return {
        "filename": filename,
        "tag": str(f"video/{vid_data.video_file.name}"),
    }


def create_audio_data(data, filename):
    data_file = SimpleUploadedFile(filename, data, content_type='audio/mpeg')
    aud_data = Video(video_file=data_file, filename=filename)
    aud_data.save()
    return {
        "filename": filename,
        "tag": str(f"video/{aud_data.video_file.name}"),
    }


@CheckLogin
@CheckUser
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
                text_datas.append(create_text_data(data, filename))
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
                img_datas.append(create_image_data(data, filename))
            if not flag:
                return_data = {
                    "files": img_datas,
                    "upload_num": len(zfile.namelist()),
                    "legal_num": i - 1,
                }
                return request_failed(20, "file sequence interrupt", 200, data=return_data)
            return request_success(img_datas)
        elif data_type == 'video':
            zfile = require(req.FILES, 'file', 'file')
            zfile = zipfile.ZipFile(zfile)
            vid_datas = []
            flag = True
            i = 1
            for i in range(1, 1 + len(zfile.namelist())):
                filename = f"{i}.mp4"
                if filename not in zfile.namelist():
                    flag = False
                    break
                data = zfile.read(f"{i}.mp4")
                vid_datas.append(create_video_data(data, filename))
            if not flag:
                return_data = {
                    "files": vid_datas,
                    "upload_num": len(zfile.namelist()),
                    "legal_num": i - 1,
                }
                return request_failed(20, "file sequence interrupt", 200, data=return_data)
            return request_success(vid_datas)
        elif data_type == 'audio':
            zfile = require(req.FILES, 'file', 'file')
            zfile = zipfile.ZipFile(zfile)
            aud_datas = []
            flag = True
            i = 1
            for i in range(1, 1 + len(zfile.namelist())):
                filename = f"{i}.mp3"
                if filename not in zfile.namelist():
                    flag = False
                    break
                data = zfile.read(f"{i}.mp3")
                aud_datas.append(create_audio_data(data, filename))
            if not flag:
                return_data = {
                    "files": aud_datas,
                    "upload_num": len(zfile.namelist()),
                    "legal_num": i - 1,
                }
                return request_failed(20, "file sequence interrupt", 200, data=return_data)
            return request_success(aud_datas)
        elif data_type == 'verify':
            zfile = require(req.FILES, 'file', 'file')
            zfile = zipfile.ZipFile(zfile)
            audit_datas = []
            flag = True
            i = 1
            for i in range(1, 1 + len(zfile.namelist())):
                if f"{i}.txt" in zfile.namelist():
                    data = zfile.read(f"{i}.txt").decode('utf-8')
                    audit_datas.append(create_text_data(data, f"{i}.txt"))
                elif f"{i}.jpg" in zfile.namelist():
                    data = zfile.read(f"{i}.jpg")
                    audit_datas.append(create_image_data(data, f"{i}.jpg"))
                elif f"{i}.mp4" in zfile.namelist():
                    data = zfile.read(f"{i}.mp4")
                    audit_datas.append(create_video_data(data, f"{i}.mp4"))
                elif f"{i}.mp3" in zfile.namelist():
                    data = zfile.read(f"{i}.mp3")
                    audit_datas.append(create_audio_data(data, f"{i}.mp3"))
                else:
                    flag = False
                    break
            if not flag:
                return_data = {
                    "files": audit_datas,
                    "upload_num": len(zfile.namelist()),
                    "legal_num": i - 1,
                }
                return request_failed(20, "file sequence interrupt", 200, data=return_data)
            return request_success(audit_datas)
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def upload_res(req: HttpRequest, user: User, task_id: int, q_id: int):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        try:
            result = require(body, "result", "string", err_msg="invalid request", err_code=1005)
        except KeyError:
            result = require(body, "result", "list", err_msg="invalid request", err_code=1005)
        task: Task = Task.objects.filter(task_id=task_id).first()
        # 处理result
        # 上传的是第q_id个问题的结果
        result = Result.objects.create(
            tag_user=user,
            tag_res=json.dumps(result),
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
                curr_tag_user: CurrentTagUser = task.current_tag_user_list.filter(tag_user=user).first()
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
                        if result.tag_res != ans.std_ans:
                            curr_tag_user.is_check_accepted = "fail"
                    if curr_tag_user.is_check_accepted == "pass":
                        user.score += task.reward_per_q * task.q_num
                        add_grow_value(user, 10)
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
@CheckUser
def get_task_question(req: HttpRequest, user: User, task_id: int, q_id: int):
    if req.method == "GET":
        # 找到task 和 question
        task = Task.objects.filter(task_id=task_id).first()
        if not task:
            return request_failed(11, "task does not exist", 404)
        question = task.questions.filter(q_id=q_id).first()
        if not question:
            return request_failed(13, "question does not exist", 404)
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


def pre_distribute(task_id: int, user: User):
    # 获取当前被分发到的user_id
    user_id = cache.get('current_user_id')
    if user_id is None:
        user_id = 1
        cache.set('current_user_id', user_id)
    task = Task.objects.filter(task_id=task_id).first()
    if not task:
        return user_id, task, request_failed(14, "task not created", 404)
    if task.publisher != user:
        return user_id, task, request_failed(15, "no distribute permission")
    # 任务没被审核通过
    if task.check_result == "wait":
        return user_id, task, request_failed(34, "task not checked")
    if task.check_result == "refuse":
        return user_id, task, request_failed(33, "refused task")
    return user_id, task, None


# 分发任务
@CheckLogin
@CheckUser
def distribute_task(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        user_id, task, err = pre_distribute(task_id, user)
        if err is not None:
            return err
        if task.current_tag_user_list.count() != 0:
            return request_failed(22, "task has been distributed")
        # 顺序分发(根据标注方的信用分从高到低分发)
        tag_users = User.objects.filter(user_type="tag").all()
        # 设定的分发用户数比可分发的用户数多
        if task.distribute_user_num > tag_users.count() - User.objects.filter(is_banned=True).all().count():
            return request_failed(21, "tag user not enough")

        # 检测分数是否足够 扣分
        if user.score < task.reward_per_q * task.q_num * task.distribute_user_num:
            return request_failed(10, "score not enough")
        else:
            user.score -= task.reward_per_q * task.q_num * task.distribute_user_num
            user.save()
        add_grow_value(user, 10)
        current_tag_user_num = 0  # 当前被分发到的用户数
        while current_tag_user_num < task.distribute_user_num:
            if user_id >= tag_users[len(tag_users) - 1].user_id:
                tag_user = tag_users[0]
                user_id = tag_user.user_id
                # 检测是否在被封禁用户列表中
                if tag_user.is_banned:
                    continue
            else:
                user_id += 1
                tag_user = tag_users.filter(user_id=user_id).first()
                while not tag_user:
                    user_id += 1
                    tag_user = tag_users.filter(user_id=user_id).first()
                # 检测是否被封禁
                if tag_user.is_banned:
                    continue
            cache.set('current_user_id', user_id)
            current_tag_user = CurrentTagUser.objects.create(tag_user=tag_user)
            task.current_tag_user_list.add(current_tag_user)
            current_tag_user_num += 1
        task.save()
        return request_success()


# 后端收到该请求后，将任务分发给另一个不在past_tag_user_list中的标注用户，并更新current_tag_user_list。若剩余可分发用户不足，则返回错误响应。
@CheckLogin
def refuse_task(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        task = Task.objects.filter(task_id=task_id).first()
        if not task.current_tag_user_list.filter(tag_user=user).exists():
            return request_failed(18, "no permission to accept")
        current_tag_user = task.current_tag_user_list.filter(tag_user=user).first()
        current_tag_user.accepted_at = -1
        current_tag_user.save()
        task.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
def accept_task(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        # 计算一天之内接受的任务数目
        acc_num = CurrentTagUser.objects.filter(
            Q(tag_user=user) & Q(accepted_at__isnull=False) & Q(accepted_at__gte=get_timestamp() - DAY)).count()
        print(acc_num)
        if acc_num >= 10:
            return request_failed(30, "accept limit")
        task = Task.objects.filter(task_id=task_id).first()
        if task.strategy == "toall":
            if task.current_tag_user_list.filter(accepted_at__gte=0).count() >= task.distribute_user_num:
                return request_failed(31, "distribution completed")
            else:
                if task.current_tag_user_list.filter(tag_user=user, accepted_at__gte=0).exists():
                    return request_failed(32, "repeat accept")
                curr_tag_user = CurrentTagUser.objects.create(tag_user=user, accepted_at=get_timestamp())
                task.current_tag_user_list.add(curr_tag_user)
                task.save()
        if task.current_tag_user_list.filter(tag_user=user).exists():
            # current user is tag_user, change accepted_time
            for current_tag_user in task.current_tag_user_list.all():
                if current_tag_user.tag_user == user:
                    current_tag_user.accepted_at = get_timestamp()
                    current_tag_user.save()
            task.save()
            for category in task.task_style.all():
                user_category, created = UserCategory.objects.get_or_create(user=user, category=category)
                user_category.count += 1
                user_category.save()
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
        if task.strategy == "toall" or task.current_tag_user_list.filter(tag_user=user).exists():
            if task.progress.filter(tag_user=user).first():
                # 已经做过这个题目
                qid = task.progress.filter(tag_user=user).first().q_id
                return request_success({"q_id": qid})
            else:
                # 这个用户还没做过这个题目
                return request_success({"q_id": 1})
        else:
            return request_failed(1006, "no access permission")
    else:
        return BAD_METHOD


# 后端判断当前用户是否已经接受任务task_id。
@CheckLogin
def is_accepted(req: HttpRequest, user: User, task_id: int):
    if req.method == "GET":
        task: Task = Task.objects.filter(task_id=task_id).first()
        if not task:
            return request_failed(14, "task not created", 404)
        # 没有分发
        if task.strategy != "toall" and task.current_tag_user_list.count() == 0:
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
            return request_failed(14, "task not created", 404)
        if task.agent:
            return request_success({"is_distributed": True})
        if task.current_tag_user_list.count() == 0:
            return request_success({"is_distributed": False})
        else:
            return request_success({"is_distributed": True})
    else:
        return BAD_METHOD


# 分发任务
@CheckLogin
@CheckUser
def redistribute_task(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        user_id, task, err = pre_distribute(task_id, user)
        if err is not None:
            return err

        update_task_tagger_list(task)
        tag_users = User.objects.filter(user_type="tag").all()
        invalid_num = task.past_tag_user_list.count()
        for ban_user in User.objects.filter(is_banned=True).all():
            if not task.past_tag_user_list.filter(user=ban_user.ban_user).exists():
                invalid_num += 1
        if task.distribute_user_num > tag_users.count() - invalid_num:
            return request_failed(21, "tag user not enough")
        current_tag_user_num = task.current_tag_user_list.count()
        while current_tag_user_num < task.distribute_user_num:
            if user_id >= tag_users[len(tag_users) - 1].user_id:
                tag_user = tag_users[0]
                user_id = tag_user.user_id

            else:
                user_id += 1
                tag_user = tag_users.filter(user_id=user_id).first()
                while not tag_user:
                    user_id += 1
                    tag_user = tag_users.filter(user_id=user_id).first()
            # 检测是否在被封禁用户列表中
            if tag_user.is_banned:
                continue
            if task.current_tag_user_list.filter(tag_user=tag_user).exists():
                continue
            if task.past_tag_user_list.filter(user_id=tag_user.user_id).exists():
                continue
            cache.set('current_user_id', user_id)
            current_tag_user = CurrentTagUser.objects.create(tag_user=tag_user)
            task.current_tag_user_list.add(current_tag_user)
            current_tag_user_num += 1
        task.save()
        return request_success()
    else:
        return BAD_METHOD


def update_task_tagger_list(task):
    current_tagger_list = task.current_tag_user_list.all()
    for current_tagger in current_tagger_list:
        if current_tagger.accepted_at is None:
            continue
        if current_tagger.accepted_at == -1:
            task.past_tag_user_list.add(current_tagger.tag_user)
            task.current_tag_user_list.remove(current_tagger)
            continue
        if current_tagger.is_finished:
            continue
        if task.total_time_limit < get_timestamp() - current_tagger.accepted_at:
            task.past_tag_user_list.add(current_tagger.tag_user)
            task.current_tag_user_list.remove(current_tagger)
    task.save()


@CheckLogin
@CheckRequire
def to_agent(req: HttpRequest, user: User, task_id: int):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        agent_id = require(body, "agent_id", "int", err_msg="invalid request", err_code=1005)
        agent = User.objects.filter(user_id=agent_id).first()
        if not agent:
            return request_failed(8, "user does not exist", 404)
        if agent.user_type != "agent":
            return request_failed(1006, "no permission")
        task = Task.objects.filter(task_id=task_id).first()
        if not task:
            return request_failed(14, "task not created", 404)
        if task.publisher != user:
            return request_failed(1006, "no permission")
        task.agent = agent
        task.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
def distribute_to_user(req: HttpRequest, user: User, task_id: int, user_id: int):
    if req.method == "POST":
        if user.user_type != "agent":
            return request_failed(1006, "no permission")
        task = Task.objects.filter(task_id=task_id).first()
        if not task:
            return request_failed(14, "task not created", 404)
        if task.current_tag_user_list.count() >= task.distribute_user_num:
            return request_failed(20, "The tasks have all been distributed")
        if task.past_tag_user_list.filter(user_id=user_id).exists():
            return request_failed(24, "user is distributed before")  # remains to be modified
        if task.current_tag_user_list.filter(tag_user=User.objects.filter(user_id=user_id).first()).exists():
            return request_failed(25, "user has been distributed")  # remains to be modified

        cur_tag_user = CurrentTagUser.objects.create(tag_user=User.objects.filter(user_id=user_id).first())
        task.current_tag_user_list.add(cur_tag_user)
        task.save()
        return request_success()
    else:
        return BAD_METHOD


@CheckLogin
@CheckRequire
def get_free_tasks(req: HttpRequest, user: User):
    if req.method == "GET":
        if user.user_type != "tag":
            return request_failed(1006, "no permission")
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
        # print("自己的category和count",[{i.category.category ,i.count} for i in usercategories])
        # for task in tasks:
        #     print([i.category for i in task.task_style.all()],f'and my_count {task.my_count}')
        left_tasks = Task.objects.filter(strategy="toall", check_result="accept").exclude(task_style__in=categories)
        return_list = [element.serialize() for element in tasks if
                       element.current_tag_user_list.count() < element.distribute_user_num] + \
                      [element.serialize() for element in left_tasks if
                       element.current_tag_user_list.count() < element.distribute_user_num]
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
        task.check_result = check_result
        task.save()
        return request_success()
    else:
        return BAD_METHOD
