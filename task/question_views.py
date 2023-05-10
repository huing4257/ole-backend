import json

from django.http import HttpRequest

from task.models import Task, Result, Question, Progress, CurrentTagUser, InputResult, InputType
from user.models import User
from user.vip_views import add_grow_value
from utils.utils_check import CheckLogin, CheckUser
from utils.utils_request import request_success, BAD_METHOD, request_failed
from utils.utils_require import CheckRequire, require


@CheckLogin
@CheckRequire
def upload_res(req: HttpRequest, user: User, task_id: int, q_id: int):
    if req.method == "POST":
        body = json.loads(req.body.decode("utf-8"))
        task: Task = Task.objects.filter(task_id=task_id).first()
        try:
            result = require(body, "result", "string", err_msg="invalid request", err_code=1005)
        except KeyError:
            result = require(body, "result", "list", err_msg="invalid request", err_code=1005)
        input_result_list = require(body, "input_result", "list", err_msg="invalid request",
                                    err_code=1005) if task.task_type == "self_define" else []
        input_result_obj_list = [InputResult.objects.create(
            input_type=InputType.objects.filter(input_tip=input_result['input_type']).first(),
            input_res=input_result['input_res']
        ) for input_result in input_result_list]
        # 处理result
        # 上传的是第q_id个问题的结果
        result = Result.objects.create(
            tag_user=user,
            tag_res=json.dumps(result),
        )
        result.input_result.set(input_result_obj_list)
        result.save()
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
                        result = question.input_res.all().filter(tag_user=user).first()
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
